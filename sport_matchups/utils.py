# utils.py
from .models import Game

def moneyline_to_implied_prob(ml):
    if ml > 0:
        return 100 / (ml + 100)
    else:
        return -ml / (-ml + 100)

def calculate_moneyline_probs(moneyA, moneyB):
    """
    Calculate true probabilities and vig from two money lines.
    Args:
        moneyA (int): Money line for team A (e.g., -150)
        moneyB (int): Money line for team B (e.g., +140)
    Returns:
        teamA, teamB, and vig percentage
    """
    impProbA = moneyline_to_implied_prob(moneyA)
    impProbB = moneyline_to_implied_prob(moneyB)
    totImpProb = impProbA + impProbB
    vig = (totImpProb - 1)
    return impProbA, impProbB, vig

# Convert moneyline odds to decimal odds
def to_decimal_odds(ml):
    if not ml or ml == 0:
        return 1
    if ml > 0:
        return (ml / 100) + 1
    return (100 / abs(ml)) + 1


def calculate_edge(home_ml, away_ml, home_pct, away_pct):
    """
    Calculate the edge and determine which side to bet on.
    Args:
        home_ml (int): Money line for home team
        away_ml (int): Money line for away team
        home_pct (float): AI-predicted probability for home team
        away_pct (float): AI-predicted probability for away team
    Returns:
        dict: {bet_side, edge_value, ml, prob}
    """

    home_decimal = to_decimal_odds(home_ml)
    away_decimal = to_decimal_odds(away_ml)

    # Calculate implied probabilities from odds
    implied_home_prob = 1 / home_decimal
    implied_away_prob = 1 / away_decimal

    # Calculate edge
    home_edge = (home_pct or 0) - implied_home_prob *100
    away_edge = (away_pct or 0) - implied_away_prob *100

    # Determine which side to bet on
    if home_edge > away_edge and home_edge > 0:
        bet_side = "home"
        edge_value = home_edge  # Convert to percentage
        ml = home_ml
        prob = home_pct
    elif away_edge > 0:
        bet_side = "away"
        edge_value = away_edge
        ml = away_ml
        prob = away_pct
    else:
        bet_side = "none"
        edge_value = 0
        ml = 0
        prob = 0

    return {"bet_side": bet_side, "edge_value": edge_value, "ml": ml, "prob": prob}

def calculate_wager(bet_side, ml, prob, bankroll):
    """
    Calculate the wager size using the Kelly Criterion.
    Args:
        bet_side (str): "home", "away", or "none"
        ml (int): Money line for the bet
        prob (float): Predicted probability
        bankroll (float): User's bankroll
    Returns:
        float: Wager amount
    """
    wager = 0
    if bet_side != "none" and bankroll > 0 and prob > 0:
        decimal_odds = (ml / 100) + 1 if ml > 0 else (100 / abs(ml)) + 1
        kelly_fraction = (prob * (decimal_odds - 1) - (1 - prob)) / (decimal_odds - 1)
        wager = max(0, min(kelly_fraction * bankroll, bankroll))  # Cap between 0 and bankroll
    return wager

def get_games_for_user(user_pref):
    qs = []
    games = Game.objects.select_related(
        'league', 'away_team', 'home_team',
        'away_team__organization', 'home_team__organization'
    ).prefetch_related('gameodds_set', 'aigameodds_set').order_by('game_date')

    for game in games:
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
            imp_away_pct, imp_home_pct, _ = calculate_moneyline_probs(
                game_odds["away_ml"], game_odds["home_ml"]
            )
            edge_data = calculate_edge(
                game_odds["home_ml"],
                game_odds["away_ml"],
                ai_odds["home_pct"],
                ai_odds["away_pct"]
            )
            if edge_data["edge_value"] >= user_pref.edge:
                # Assume bankroll is in user preferences or use a default
                bankroll = getattr(user_pref, "bankroll", 1000)  # Default bankroll $1000
                wager = calculate_wager(
                    edge_data["bet_side"],
                    edge_data["ml"],
                    edge_data["prob"]/100,
                    bankroll
                )
                qs.append({
                    "game": game,
                    "bet_side": edge_data["bet_side"],
                    "edge_value": edge_data["edge_value"],
                    "ml": edge_data["ml"],
                    "implied_prob": (1 / to_decimal_odds(edge_data["ml"])) * 100 if edge_data["ml"] else 0,
                    "wager": wager
                })
    return sorted(qs, key=lambda x: x['edge_value'], reverse=True)[:5]  # Limit to 5 games
