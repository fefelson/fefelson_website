from django.shortcuts import render, redirect
from django.utils import timezone
from django.templatetags.static import static
from .models import Game, GameOdds, AIGameOdds, Team, Organization, TeamStat, Stat
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login

from .utils import calculate_moneyline_probs



def game_list(request):
    # --- existing game building code ---
    games = Game.objects.select_related(
        'league', 'away_team', 'home_team',
        'away_team__organization', 'home_team__organization'
    ).prefetch_related('gameodds_set', 'aigameodds_set').order_by('game_date')

    game_data = []
    for game in games:
        away_logo = static(f'images/logos/{game.away_team.organization.org_id}.png')
        home_logo = static(f'images/logos/{game.home_team.organization.org_id}.png')

        game_odds = {}
        if game.gameodds_set.exists():
            odds = game.gameodds_set.first()
            game_odds = {
                'book_name': odds.book.name,
                'away_ml': odds.away_ml,
                'home_ml': odds.home_ml,
                'spread': odds.spread
            }
        ai_odds = {}
        if game.aigameodds_set.exists():
            ai_odds_instance = game.aigameodds_set.first()
            ai_odds = {
                'ai_name': ai_odds_instance.ai.name,
                'away_pct': ai_odds_instance.away_pct,
                'home_pct': ai_odds_instance.home_pct
            }
        if game_odds and ai_odds:
            impAwayPct, impHomePct, vig = calculate_moneyline_probs(game_odds["away_ml"], game_odds["home_ml"])
            game_odds["away_pct"] = impAwayPct * 100
            game_odds["home_pct"] = impHomePct * 100
            game_odds["vig"] = vig * 100

            awayEdge = ai_odds["away_pct"] - game_odds["away_pct"]
            homeEdge = ai_odds["home_pct"] - game_odds["home_pct"]
            edge = max(awayEdge, homeEdge)

            game_data.append({
                'game_id': game.game_id,
                'league': game.league.name,
                'away_team': {'name': game.away_team.organization.abrv, 'logo': away_logo},
                'home_team': {'name': game.home_team.organization.abrv, 'logo': home_logo},
                'game_date': game.game_date,
                'game_odds': game_odds,
                'ai_odds': ai_odds,
                'edge': edge,
            })

    # --- preferences injection ---
    preferences = None
    if request.user.is_authenticated and hasattr(request.user, "preferences"):
        preferences = {
            "edge": request.user.preferences.edge,
            "bankroll": request.user.preferences.bankroll,
        }

    context = {
        'games': game_data,
        'preferences': preferences,
    }
    return render(request, "sport_matchups/game_list.html", context)


def game_detail(request, game_id):
    game = get_object_or_404(
        Game.objects.select_related(
            'league', 'away_team', 'home_team',
            'away_team__organization', 'home_team__organization'
        ).prefetch_related('gameodds_set', 'aigameodds_set'),
        game_id=game_id
    )

    team_stats = {
        'home': TeamStat.objects.filter(team=game.home_team).select_related('stat').order_by('stat__name'),
        'away': TeamStat.objects.filter(team=game.away_team).select_related('stat').order_by('stat__name')
    }

    logos = {
        'away': static(f'images/logos/{game.away_team.organization.org_id}.png'),
        'home': static(f'images/logos/{game.home_team.organization.org_id}.png')
    }

    game_odds = {}
    if game.gameodds_set.exists():
        odds = game.gameodds_set.first()
        impAwayPct, impHomePct, vig = calculate_moneyline_probs(odds.away_ml, odds.home_ml)
        game_odds = {
            'book_name': odds.book.name,
            'away_ml': odds.away_ml,
            'home_ml': odds.home_ml,
            'spread': odds.spread,
            'away_pct': impAwayPct * 100,
            'home_pct': impHomePct * 100,
            'vig': vig * 100,
        }

    ai_odds = {}
    if game.aigameodds_set.exists():
        ai_odds_instance = game.aigameodds_set.first()
        ai_odds = {
            'ai_name': ai_odds_instance.ai.name,
            'away_pct': ai_odds_instance.away_pct,
            'home_pct': ai_odds_instance.home_pct,
        }

    stat_keys = ["pts", "rush_yards", "pass_yards", "turns", "penalty_yards", "sack_yds_lost"]
    stats = {"away": {}, "home": {}}

    for a_h in ("away", "home"):
        stats[a_h]["stats_dict"] = {ts.stat.name: ts for ts in team_stats[a_h]}
        stats[a_h]["stat_pairs"] = []
        for key in stat_keys:
            off_stat = stats[a_h]["stats_dict"].get(f"off_{key}")
            def_stat = stats[a_h]["stats_dict"].get(f"def_{key}")
            stats[a_h]["stat_pairs"].append({
                'stat': key,
                'off_score': off_stat.score * 100 if off_stat else 0,
                'off_color': off_stat.color if off_stat else '#CCCCCC',
                'def_score': def_stat.score * 100 if def_stat else 0,
                'def_color': def_stat.color if def_stat else '#CCCCCC',
            })

    game_data = {
        'game_id': game.game_id,
        'league': game.league.name,
        'game_date': game.game_date,
        'game_odds': game_odds,
        'ai_odds': ai_odds,
        'away_team': {'name': game.away_team.organization.abrv, 'logo': logos['away'], "stats": stats['away']},
        'home_team': {'name': game.home_team.organization.abrv, 'logo': logos['home'], "stats": stats['home']},
    }

    # --- preferences injection ---
    preferences = None
    if request.user.is_authenticated and hasattr(request.user, "preferences"):
        preferences = {
            "edge": request.user.preferences.edge,
            "bankroll": request.user.preferences.bankroll,
        }

    template_map = {
        'NFL': 'sport_matchups/football_game_detail.html',
        'NCAAF': 'sport_matchups/football_game_detail.html',
    }
    template_name = template_map.get(game.league.name, 'sport_matchups/game_detail.html')
    return render(request, template_name, {'game_data': game_data, 'preferences': preferences})
