from django.contrib.auth.models import AbstractUser
from django.db import models


class League(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Organization(models.Model):
    class OrganizationRole(models.TextChoices):
        PRO = "PRO", "Pro"
        COLLEGE = "COLLEGE", "College"

    org_id = models.SlugField(max_length=5, unique=True)
    abrv = models.CharField(max_length=7)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    color_primary = models.CharField(max_length=8)
    color_secondary = models.CharField(max_length=8)
    role = models.CharField(max_length=10, choices=OrganizationRole.choices)

    def __str__(self):
        return f"{self.abrv} ({self.first_name} {self.last_name})"


class Team(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    league = models.ForeignKey(League, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.organization.abrv} - {self.league.name}"


class Game(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    game_id = models.CharField(max_length=100, unique=True)
    game_date = models.DateTimeField()
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="away_games")
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="home_games")

    def __str__(self):
        return f"{self.away_team} vs {self.home_team} ({self.game_date})"


class StartingPitcher(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    throws = models.CharField(max_length=1)
    player_id = models .IntegerField()

    def __str__(self):
        return f"{self.team} -- {self.name} {self.throws}"


class SportsBook(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


class GameOdds(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    book = models.ForeignKey(SportsBook, on_delete=models.CASCADE)
    away_ml = models.IntegerField()
    home_ml = models.IntegerField()
    spread = models.FloatField()

    def __str__(self):
        return f"{self.game.game_id} Odds: {self.away_ml}/{self.home_ml}, Spread {self.spread}"



class AI(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


class AIGameOdds(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    ai = models.ForeignKey(AI, on_delete=models.CASCADE)
    away_pct = models.FloatField()
    home_pct = models.FloatField()

    class Meta:
        unique_together = ("ai", "game")

    def __str__(self):
        return f"{self.game} - {self.ai.name}: {self.away_pct} / {self.home_pct}"



class Stat(models.Model):
    """A stat definition (like OBP, SLG, HR%)."""
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.league} {self.name}"


class TeamStat(models.Model):
    """Links a team to a stat definition with its specific value."""
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    stat = models.ForeignKey(Stat, on_delete=models.CASCADE)
    score = models.FloatField()
    color = models.CharField(max_length=30)
    label = models.CharField(max_length=30)

    class Meta:
        unique_together = ("team", "stat")

    def __str__(self):
        return f"{self.team} - {self.stat.name}"


class Preferences(models.Model):
    user = models.OneToOneField(
        "User",  # forward reference, since User is defined later
        on_delete=models.CASCADE,
        related_name="preferences"
    )
    edge = models.FloatField()
    bankroll = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} Prefs (edge={self.edge}, bankroll={self.bankroll})"



class User(AbstractUser):
    send_email = models.BooleanField(default=True)

    def __str__(self):
        return self.username
