// filter_games.js
export function populateLeagueFilter(games, leagueFilter) {
    const leagues = new Set();
    games.forEach(game => {
        const league = game.dataset.league;
        if (league) leagues.add(league);
    });

        leagues.forEach(league => {
            const option = document.createElement("option");
            option.value = league;
            option.textContent = league;
            leagueFilter.appendChild(option);
        });
}

// Format date in Eastern Time as YYYY-MM-DD
export function formatDateET(date) {
    const options = {
        timeZone: "America/New_York",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
    };
    return new Intl.DateTimeFormat("en-CA", options).format(date); // YYYY-MM-DD
}

// Parse game date safely from ISO string or YYYY-MM-DD
function parseGameDate(dateString) {
    const d = new Date(dateString);
    if (isNaN(d)) {
        throw new Error("Invalid date string: " + dateString);
    }
    return d;
}

export function isTodayET(dateString) {
    try {
        const gameDate = parseGameDate(dateString);
        const gameStr = formatDateET(gameDate);
        const todayStr = formatDateET(new Date());
        return gameStr === todayStr;
    } catch (e) {
        console.error(`Invalid date format: ${dateString}`, e);
        return false;
    }
}

export function isFutureET(dateString) {
    try {
        const gameDate = parseGameDate(dateString);
        const gameStr = formatDateET(gameDate);
        const todayStr = formatDateET(new Date());
        return gameStr > todayStr;
    } catch (e) {
        console.error(`Invalid date format: ${dateString}`, e);
        return false;
    }
}

export function filterGames(games, leagueFilter, dateFilter, selectedEdge) {
    const selectedLeague = leagueFilter.value || "all";
    const selectedDate = dateFilter.value || "all";
    const visibleGames = [];

    games.forEach(game => {
        const rawEdge = game.getAttribute("data-edge");
        const gameEdge = rawEdge !== null ? parseFloat(rawEdge) : -Infinity;
        const gameLeague = game.dataset.league || "";
        const gameDate = game.dataset.date;

        let reason = null;

        // League filter
        const leagueMatch = selectedLeague === "all" || gameLeague === selectedLeague;
        if (!leagueMatch) reason = `league mismatch (${gameLeague} vs ${selectedLeague})`;

        // Date filter
        let dateMatch = true;
        if (selectedDate !== "all") {
            try {
                if (selectedDate === "today") {
                    dateMatch = isTodayET(gameDate);
                    if (!dateMatch) reason = `not today (${gameDate})`;
                } else if (selectedDate === "future") {
                    dateMatch = isFutureET(gameDate);
                    if (!dateMatch) reason = `not future (${gameDate})`;
                }
            } catch (e) {
                console.error(`Invalid date format for game: ${gameDate}`, e);
                dateMatch = false;
                reason = "invalid date format";
            }
        }

        // Edge filter
        if (gameEdge < selectedEdge) {
            reason = `edge too low (${gameEdge} < ${selectedEdge})`;
        }

        // Apply filters
        if (gameEdge >= selectedEdge && leagueMatch && dateMatch) {
            game.style.display = "flex";
            visibleGames.push(game);

        } else {
            game.style.display = "none";
        }
    });

    return visibleGames;
}
