// game_list.js
import { populateLeagueFilter, filterGames } from './filter_games.js';
import { calculateEdge, calculateWager } from './kelly_wager.js';
import { updateGameDisplay } from './game_display.js';

document.addEventListener("DOMContentLoaded", function() {
    const edgeSelect = document.getElementById("edge-select");
    const bankrollSelect = document.getElementById("bankroll-select");
    const leagueFilter = document.getElementById("leagueFilter");
    const dateFilter = document.getElementById("dateFilter");
    const games = document.querySelectorAll(".game");

    // Initialize league filter
    populateLeagueFilter(games, leagueFilter);

    // Initialize edge and bankroll from userPreferences
    if (window.userPreferences) {
        if (edgeSelect && window.userPreferences.edge !== undefined) {
            const edgeOptions = Array.from(edgeSelect.options).map(opt => parseFloat(opt.value));
            const closestEdge = edgeOptions.reduce((prev, curr) =>
            Math.abs(curr - window.userPreferences.edge) < Math.abs(prev - window.userPreferences.edge) ? curr : prev
            );
            edgeSelect.value = closestEdge;
        }
        if (bankrollSelect && window.userPreferences.bankroll !== undefined) {
            const bankrollOptions = Array.from(bankrollSelect.options).map(opt => parseFloat(opt.value));
            const closestBankroll = bankrollOptions.reduce((prev, curr) =>
            Math.abs(curr - window.userPreferences.bankroll) < Math.abs(prev - window.userPreferences.bankroll) ? curr : prev
            );
            bankrollSelect.value = closestBankroll;
        }
    }

    // Get current edge and bankroll values
    const getEdge = () => edgeSelect ? parseFloat(edgeSelect.value) || 0 : (window.userPreferences?.edge !== undefined ? parseFloat(window.userPreferences.edge) : 0);
    const getBankroll = () => bankrollSelect ? parseFloat(bankrollSelect.value) || 1000 : (window.userPreferences?.bankroll !== undefined ? parseFloat(window.userPreferences.bankroll) : 1000);

    // Function to update games based on filters and display
    const updateGames = () => {
        const selectedEdge = getEdge();
        const bankroll = getBankroll();
        const visibleGames = filterGames(games, leagueFilter, dateFilter, selectedEdge);

        visibleGames.forEach(game => {
            // Validate dataset attributes
            const odds = game.dataset.odds ? game.dataset.odds.split(",").map(Number) : [0, 0];
            const ai = game.dataset.ai ? game.dataset.ai.split(",").map(x => parseFloat(x) / 100.0) : [0, 0];

            // Ensure valid numbers
            const [home_ml, away_ml] = odds.every(n => !isNaN(n)) ? odds : [0, 0];
            const [home_pct, away_pct] = ai.every(n => !isNaN(n)) ? ai : [0, 0];

            const { betSide, edgeValue, ml, prob } = calculateEdge(home_ml, away_ml, home_pct, away_pct);
            const wager = calculateWager(betSide, ml, prob, bankroll);
            updateGameDisplay(game, betSide, edgeValue, wager, ml, prob);
        });
    };

    // Run filter on load
    try {
        updateGames();
    } catch (e) {
        console.error("Error updating games on load:", e);
    }

    // Add event listeners
    if (edgeSelect) edgeSelect.addEventListener("change", updateGames);
    if (bankrollSelect) bankrollSelect.addEventListener("change", updateGames);
    leagueFilter.addEventListener("change", updateGames);
    dateFilter.addEventListener("change", updateGames);
});
