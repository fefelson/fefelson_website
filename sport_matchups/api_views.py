from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication

from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from datetime import datetime
import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from .utils import get_games_for_user
from .emails import send_user_email

from .models import (Game, GameOdds, Team, League, AI, AIGameOdds, User,
                     SportsBook, Stat, TeamStat, StartingPitcher, Preferences)


from django.utils import timezone

logger = logging.getLogger(__name__)

# -------------------------
# Login / Logout
# -------------------------
class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class Logout(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        return Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)

# -------------------------
# Serializers
# -------------------------
class GameSerializer(serializers.ModelSerializer):
    away_team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    home_team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    league = serializers.SlugRelatedField(slug_field='name', queryset=League.objects.all())

    class Meta:
        model = Game
        fields = ['game_id', 'game_date', 'league', 'away_team', 'home_team']


class GameOddsSerializer(serializers.ModelSerializer):
    game = serializers.PrimaryKeyRelatedField(queryset=Game.objects.all())

    class Meta:
        model = GameOdds
        fields = ['game', 'away_ml', 'home_ml', 'spread']


class TeamStatSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    stat = serializers.PrimaryKeyRelatedField(queryset=Stat.objects.all())

    class Meta:
        model = TeamStat
        fields = ['team', 'stat', 'score', 'color']


class StatSerializer(serializers.ModelSerializer):
    league = serializers.SlugRelatedField(slug_field='name', queryset=League.objects.all())
    class Meta:
        model = Stat
        fields = ['league', 'name']


class AIGameOddsSerializer(serializers.ModelSerializer):
    game = serializers.PrimaryKeyRelatedField(queryset=Game.objects.all())
    ai = serializers.SlugRelatedField(slug_field='name', queryset=AI.objects.all())

    class Meta:
        model = AIGameOdds
        fields = ['game', 'ai', 'away_pct', 'home_pct']

    def validate(self, data):
        if abs(data['away_pct'] + data['home_pct'] - 100.0) > 0.01:
            raise serializers.ValidationError("away_pct and home_pct must sum to 100%")
        return data

# -------------------------
# Game ViewSet with bulk create/update/delete
# -------------------------
class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def create(self, request):
        """
        Accepts a list of games with optional odds and AI odds.
        Uses update_or_create so that existing rows get updated.
        """
        games = request.data.get("games", [])
        if not isinstance(games, list):
            return Response({"error": "'games' must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        created_games, updated_games, errors = [], [], []

        for g in games:
            try:
                # -------------------------
                # Game (update_or_create)
                # -------------------------
                league = League.objects.get(name=g['leagueId'])
                home_team = Team.objects.get(id=g['homeId'])
                away_team = Team.objects.get(id=g['awayId'])

                game_obj, created = Game.objects.update_or_create(
                    game_id=g['title'],
                    defaults={
                        'game_date': g['gameTime'],
                        'league': league,
                        'home_team': home_team,
                        'away_team': away_team,
                    }
                )
                serialized_game = GameSerializer(game_obj).data
                if created:
                    created_games.append(serialized_game)
                else:
                    updated_games.append(serialized_game)

                # -------------------------
                # GameOdds (latest odds only)
                # -------------------------
                latest_odds = g.get("odds", [{}])
                if latest_odds:
                    book = SportsBook.objects.get(name="MGM")
                    GameOdds.objects.update_or_create(
                        game=game_obj,
                        book=book,
                        defaults={
                            'home_ml': latest_odds[-1].get('home_ml'),
                            'away_ml': latest_odds[-1].get('away_ml'),
                            'spread': latest_odds[-1].get('home_spread'),
                        }
                    )

                # -------------------------
                # AI Odds (hardcoded ESPN example)
                # -------------------------
                if "predictor" in g:
                    ai = AI.objects.get(name="ESPN")
                    AIGameOdds.objects.update_or_create(
                        game=game_obj,
                        ai=ai,
                        defaults={
                            'away_pct': g["predictor"][0][1],
                            'home_pct': g["predictor"][1][1],
                        }
                    )

                # -------------------------
                # (Optional) Baseball details
                # -------------------------
                if g.get("home_pitcher") or g.get("away_pitcher"):
                    # Requires BaseballGameDetails model (separate table, OneToOne with Game)
                    from .models import BaseballGameDetails, Player
                    home_pitcher = Player.objects.filter(id=g.get("home_pitcher")).first()
                    away_pitcher = Player.objects.filter(id=g.get("away_pitcher")).first()
                    BaseballGameDetails.objects.update_or_create(
                        game=game_obj,
                        defaults={
                            "home_pitcher": home_pitcher,
                            "away_pitcher": away_pitcher,
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing game {g.get('title')}: {e}", exc_info=True)
                errors.append({"game": g.get('title'), "error": str(e)})

        response = {
            "created_games": created_games,
            "updated_games": updated_games,
            "errors": errors
        }
        status_code = status.HTTP_200_OK if created_games or updated_games else status.HTTP_400_BAD_REQUEST
        return Response(response, status=status_code)

    @action(detail=False, methods=['post'], url_path='set')
    def set_games(self, request):
        return self.create(request)


    @action(detail=False, methods=['post'], url_path='delete')
    def delete_past_games(self, request):
        """Delete all games with a game_date in the past"""
        deleted, _ = Game.objects.filter(game_date__lt=timezone.now()).delete()
        return Response({"deleted_count": deleted}, status=status.HTTP_200_OK)



# -------------------------
# Team ViewSet with bulk create/update/delete
# -------------------------
class TeamStatViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamStatSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def create(self, request):
        """
        Accepts a list of games with optional odds and AI odds.
        Uses update_or_create so that existing rows get updated.
        """
        teamStats = request.data.get("team_stats", [])
        if not isinstance(teamStats, list):
            return Response({"error": "'team_stats' must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        created_stats, updated_stats, errors = [], [], []

        for ts in teamStats:
            try:
                # -------------------------
                # Stat (update_or_create)
                # -------------------------
                league = League.objects.get(name=ts['league'])

                stat_obj, created = Stat.objects.update_or_create(
                    league=league,
                    name=ts['name'],
                    defaults={
                    }
                )
                serialized_stat = StatSerializer(stat_obj).data


                # -------------------------
                # TeamStats
                # -------------------------
                team = Team.objects.get(id=ts['teamId'])

                team_stat, created = TeamStat.objects.update_or_create(
                    stat=stat_obj,
                    team=team,
                    defaults={
                        'score': ts["score"],
                        'color': ts["color"],
                    }
                )
                if created:
                    created_stats.append(TeamStatSerializer(team_stat).data)
                else:
                    updated_stats.append(TeamStatSerializer(team_stat).data)




            except Exception as e:
                logger.error(f"Error processing stat {ts.get('name')}: {e}", exc_info=True)
                errors.append({"stats": ts.get('name'), "error": str(e)})

        status_code = status.HTTP_200_OK if created_stats or updated_stats else status.HTTP_400_BAD_REQUEST
        response = {
            "created_stats": created_stats,
            "updated_stats": updated_stats,
            "errors": errors
        }
        return Response(response, status=status_code)

    @action(detail=False, methods=['post'], url_path='set')
    def set_teams(self, request):
        return self.create(request)




@api_view(["POST"])
@permission_classes([IsAdminUser])  # Only admins can trigger this
def send_email_notifications(request):
    # Filter users that want emails
    users = User.objects.filter(send_email=True).select_related("preferences")
    sent_count, skipped_count = 0, 0

    for user in users:
        prefs = getattr(user, "preferences", None)  # Safe access
        if not prefs:
            skipped_count += 1
            continue

        games = get_games_for_user(prefs)
        if send_user_email(user, games):
            sent_count += 1
        else:
            skipped_count += 1

    return Response({
        "status": "done",
        "emails_sent": sent_count,
        "emails_skipped": skipped_count,
    })



