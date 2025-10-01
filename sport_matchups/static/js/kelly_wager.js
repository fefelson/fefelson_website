// kelly_wager.js
export function calculateEdge(home_ml, away_ml, home_pct, away_pct) {
    // Convert moneyline odds to decimal odds
    const toDecimalOdds = (ml) => {
        if (isNaN(ml) || ml === 0) return 1;
        if (ml > 0) return (ml / 100) + 1;
        return (100 / Math.abs(ml)) + 1;
    };
    const homeDecimal = toDecimalOdds(home_ml);
    const awayDecimal = toDecimalOdds(away_ml);

    // Calculate implied probabilities from odds
    const impliedHomeProb = (1 / homeDecimal);
    const impliedAwayProb = (1 / awayDecimal);

    // Calculate edge
    const homeEdge = (home_pct || 0) - impliedHomeProb;
    const awayEdge = (away_pct || 0) - impliedAwayProb;


    // Determine which side to bet on
    let betSide, edgeValue, ml, prob;
    if (homeEdge > awayEdge && homeEdge > 0) {
        betSide = "home";
        edgeValue = homeEdge * 100; // Convert to percentage
        ml = home_ml;
        prob = home_pct;
    } else if (awayEdge > 0) {
        betSide = "away";
        edgeValue = awayEdge * 100;
        ml = away_ml;
        prob = away_pct;
    } else {
        betSide = "none";
        edgeValue = 0;
        ml = 0;
        prob = 0;
    }

    return { betSide, edgeValue, ml, prob };
}

export function calculateWager(betSide, ml, prob, bankroll) {
    let wager = 0;
    if (betSide !== "none" && bankroll > 0 && prob > 0 && !isNaN(prob)) {
        const decimalOdds = ml > 0 ? (ml / 100) + 1 : (100 / Math.abs(ml)) + 1;
        const kellyFraction = (prob * (decimalOdds - 1) - (1 - prob)) / (decimalOdds - 1);
        wager = Math.max(0, Math.min(kellyFraction * bankroll, bankroll)); // Cap between 0 and bankroll
    }
    return wager;
}
