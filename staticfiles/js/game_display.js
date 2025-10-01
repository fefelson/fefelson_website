// game_display.js
export function updateGameDisplay(game, betSide, edgeValue, wager, ml, prob) {
    const edgeTeamElement = game.querySelector(".edge-team");
    const betAmountElement = game.querySelector(".bet-amount");
    const betMLElement = game.querySelector(".edge-bet");
    const bookPctElement = game.querySelector(".book-pct");
    const aiPctElement = game.querySelector(".ai-pct");
    const awayOddsEl = game.querySelector(".away-odds");
    const homeOddsEl = game.querySelector(".home-odds");

    // Update edge team
    if (edgeTeamElement) {
        edgeTeamElement.textContent = betSide === "home" ? game.querySelector(".home-team p")?.textContent || "TBD" :
        betSide === "away" ? game.querySelector(".away-team p")?.textContent || "TBD" : "TBD";
    } else {
        console.warn(`Missing edge-team element for game:`, game);
    }

    // Update betML
    if (betMLElement) {
        betMLElement.textContent = ml > 0 && !isNaN(ml) ? `+${ml}` : ml;
    } else {
        console.warn(`Missing win-pct element for game:`, game);
    }

    // Update bet amount
    if (betAmountElement) {
        betAmountElement.textContent = isNaN(wager) ? "$0.00" : `$${wager.toFixed(2)}`;
    } else {
        console.warn(`Missing bet-amount element for game:`, game);
    }

    // Update book percentage
    if (bookPctElement) {
        bookPctElement.textContent = `${(prob*100-edgeValue).toFixed(1)}`;
    }

    // Update ai percentage
    if (aiPctElement) {
        aiPctElement.textContent = `${(edgeValue).toFixed(2)}`;
    }

    // Update odds colors
    if (awayOddsEl && homeOddsEl) {
        if (betSide === "away") {
            awayOddsEl.style.color = "gold";
            homeOddsEl.style.color = "red";
        } else if (betSide === "home") {
            homeOddsEl.style.color = "gold";
            awayOddsEl.style.color = "red";
        } else {
            awayOddsEl.style.color = "";
            homeOddsEl.style.color = "";
        }
    } else {
        console.warn(`Missing odds elements for game:`, game);
    }
}
