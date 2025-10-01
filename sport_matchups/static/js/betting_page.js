// bettingPage.js
import * as kellyWager from './kellyWager.js';

document.addEventListener("DOMContentLoaded", function() {
    const bankrollSelect = document.getElementById("bankroll-select");
    const games = document.querySelectorAll(".game");

    function updateBets() {
        const bankroll = parseInt(bankrollSelect.value);
        games.forEach(game => {
            const [home_ml, away_ml] = game.dataset.odds.split(",").map(Number);
            const [home_pct, away_pct] = game.dataset.ai.split(",").map(x => parseFloat(x) / 100.0);
            const { betSide, edgeValue, ml, prob } = kellyWager.calculateEdge(home_ml, away_ml, home_pct, away_pct);
            kellyWager.updateGameDisplay(game, betSide, edgeValue, ml, prob, bankroll);
            game.style.display = "flex"; // Always show games on betting page
        });
    }

    updateBets(); // Run on load
    bankrollSelect.addEventListener("change", updateBets);
});
