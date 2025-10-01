// game_detail.js
import { calculateEdge, calculateWager } from './kelly_wager.js';

// Function to convert moneyline to implied probability (returns decimal, e.g., 0.55)
function toImpliedProbability(ml) {
    if (isNaN(ml) || ml === 0) {
        console.warn(`Invalid moneyline value: ${ml}`);
        return 0;
    }
    const decimalOdds = ml > 0 ? (ml / 100) + 1 : (100 / Math.abs(ml)) + 1;
    return 1 / decimalOdds;
}

document.addEventListener("DOMContentLoaded", function() {
    // Select DOM elements
    const edgeSelect = document.getElementById("edge-select");
    const bankrollSelect = document.getElementById("bankroll-select");
    const gameDetail = document.querySelector('.odds-header');
    const homeMlInput = document.querySelector('#home-ml-input');
    const awayMlInput = document.querySelector('#away-ml-input');
    const homeAiPctInput = document.querySelector('#home-ai-pct-input');
    const awayAiPctInput = document.querySelector('#away-ai-pct-input');
    const homeImpliedProb = document.querySelector('#home-implied-prob');
    const awayImpliedProb = document.querySelector('#away-implied-prob');
    const homeEdgeWager = document.querySelector('#home-edge-wager');
    const awayEdgeWager = document.querySelector('#away-edge-wager');

    // Validate required DOM elements
    if (!gameDetail || !homeMlInput || !awayMlInput || !homeAiPctInput || !awayAiPctInput ||
        !homeImpliedProb || !awayImpliedProb || !homeEdgeWager || !awayEdgeWager) {
        console.error('Required DOM elements missing:', {
            gameDetail, homeMlInput, awayMlInput, homeAiPctInput, awayAiPctInput,
            homeImpliedProb, awayImpliedProb, homeEdgeWager, awayEdgeWager
        });
    return;
        }


        // Get current edge and bankroll values
        const getEdge = () => edgeSelect ? parseFloat(edgeSelect.value) || 0 : (window.userPreferences?.edge !== undefined ? parseFloat(window.userPreferences.edge) : 0);

        // Get current bankroll value
        const getBankroll = () => {
            const bankrollValue = bankrollSelect ? parseFloat(bankrollSelect.value) : (window.userPreferences?.bankroll !== undefined ? parseFloat(window.userPreferences.bankroll) : 1000);
            if (isNaN(bankrollValue)) {
                console.warn('Invalid bankroll value, defaulting to 1000');
                return 1000;
            }
            return bankrollValue;
        };

        // Get current values
        const getValues = () => {
            const homeMl = parseFloat(homeMlInput.value) || 0;
            const awayMl = parseFloat(awayMlInput.value) || 0;
            const homePct = (parseFloat(homeAiPctInput.value) || 50) / 100;
            const awayPct = (parseFloat(awayAiPctInput.value) || 50) / 100;
            const bankroll = getBankroll();
            const minEdge = getEdge();
            return { homeMl, awayMl, homePct, awayPct, bankroll, minEdge };
        };

        // Initialize edge and bankroll from userPreferences
        if (window.userPreferences) {
            if (edgeSelect && window.userPreferences.edge !== undefined) {
                const edgeOptions = Array.from(edgeSelect.options || []).map(opt => parseFloat(opt.value));
                if (edgeOptions.length > 0) {
                    const closestEdge = edgeOptions.reduce((prev, curr) =>
                    Math.abs(curr - window.userPreferences.edge) < Math.abs(prev - window.userPreferences.edge) ? curr : prev
                    );
                    edgeSelect.value = closestEdge;
                }
            }
            if (bankrollSelect && window.userPreferences.bankroll !== undefined) {
                const bankrollOptions = Array.from(bankrollSelect.options || []).map(opt => parseFloat(opt.value));
                if (bankrollOptions.length > 0) {
                    const closestBankroll = bankrollOptions.reduce((prev, curr) =>
                    Math.abs(curr - window.userPreferences.bankroll) < Math.abs(prev - window.userPreferences.bankroll) ? curr : prev
                    );
                    bankrollSelect.value = closestBankroll;
                }
            }
        }

        // Function to update calculations and display
        const updateCalculations = (triggeredBy = null) => {
            const { homeMl, awayMl, homePct, awayPct, bankroll, minEdge } = getValues();

            // Synchronize AI percentages to total 100%
            if (triggeredBy === 'home-ai-pct-input' && !isNaN(parseFloat(homeAiPctInput.value))) {
                const newHomePct = Math.min(Math.max(parseFloat(homeAiPctInput.value), 0), 100);
                homeAiPctInput.value = newHomePct.toFixed(2);
                awayAiPctInput.value = (100 - newHomePct).toFixed(2);
            } else if (triggeredBy === 'away-ai-pct-input' && !isNaN(parseFloat(awayAiPctInput.value))) {
                const newAwayPct = Math.min(Math.max(parseFloat(awayAiPctInput.value), 0), 100);
                awayAiPctInput.value = newAwayPct.toFixed(2);
                homeAiPctInput.value = (100 - newAwayPct).toFixed(2);
            }

            // Recalculate percentages after synchronization
            const updatedHomePct = (parseFloat(homeAiPctInput.value) || 50) / 100;
            const updatedAwayPct = (parseFloat(awayAiPctInput.value) || 50) / 100;

            // Calculate implied probabilities
            const homeProb = toImpliedProbability(homeMl);
            const awayProb = toImpliedProbability(awayMl);

            // Update implied probability displays
            homeImpliedProb.textContent = `${(homeProb * 100).toFixed(2)}%`;
            awayImpliedProb.textContent = `${(awayProb * 100).toFixed(2)}%`;

            // Calculate edge and wager
            let betSide, edgeValue, ml, prob, wager;
            try {
                ({ betSide, edgeValue, ml, prob } = calculateEdge(homeMl, awayMl, updatedHomePct, updatedAwayPct));
                wager = calculateWager(betSide, ml, prob, bankroll);
            } catch (e) {
                console.error('Error calculating edge or wager:', e);
                return;
            }

            // Log for debugging
            console.log('Calculation results:', { betSide, edgeValue, ml, prob, wager, minEdge, bankroll, triggeredBy });

            // Reset edge/wager displays
            homeEdgeWager.style.display = 'none';
            awayEdgeWager.style.display = 'none';

            // Update edge and wager displays only if edge exceeds minEdge
            let targetEdgeDisplay, targetWagerDisplay;
            if (edgeValue >= minEdge) { // Compare as decimals
                if (betSide === 'home') {
                    homeEdgeWager.style.display = 'block';
                    targetEdgeDisplay = homeEdgeWager.querySelector('#bet-edge');
                    targetWagerDisplay = homeEdgeWager.querySelector('#wager-amount');
                } else if (betSide === 'away') {
                    awayEdgeWager.style.display = 'block';
                    targetEdgeDisplay = awayEdgeWager.querySelector('#bet-edge');
                    targetWagerDisplay = awayEdgeWager.querySelector('#wager-amount');
                }
            }

            // Update edge and wager values if applicable
            if (targetEdgeDisplay && targetWagerDisplay) {
                targetEdgeDisplay.textContent = `${(edgeValue ).toFixed(2)}%`;
                targetWagerDisplay.textContent = wager.toFixed(2);
            } else {
                console.log('No significant edge found; hiding edge/wager displays');
            }
        };

        // Run initial calculation
        try {
            updateCalculations('initial');
        } catch (e) {
            console.error('Error updating calculations on load:', e);
        }

        // Add event listeners for input changes
        const inputs = [
            { element: homeMlInput, id: 'home-ml-input' },
            { element: awayMlInput, id: 'away-ml-input' },
            { element: homeAiPctInput, id: 'home-ai-pct-input' },
            { element: awayAiPctInput, id: 'away-ai-pct-input' },
            { element: edgeSelect, id: 'edge-select' },
            { element: bankrollSelect, id: 'bankroll-select' }
        ];

        inputs.forEach(({ element, id }) => {
            if (element) {
                element.addEventListener('change', () => {
                    console.log(`Event triggered by: ${id}`);
                    updateCalculations(id);
                });
            } else {
                console.warn(`Element not found for ID: ${id}`);
            }
        });
});
