document.addEventListener('DOMContentLoaded', () => {
    const div_table_body = document.getElementById('history-table-body');

    fetch(`./api/user_games`)
        .then(response => response.json())
        .then(response_json => {
            drawStat(response_json.games_total, response_json.games_won);
            drawGames(response_json.games);
        });
    function drawGames(games) {
        for (let game of games) {
            let tr = document.createElement('tr');
            switch (game.status) {
                case 'running':
                case 'created':
                    tr.className = 'table-success';
                    break;
                default:
                    break;
            }
            let th = document.createElement('th');
            th.scope = 'row';
            th.innerText = game.id;
            tr.append(th);

            let td_name = document.createElement('td');
            td_name.innerText = game.name;
            tr.append(td_name);

            let td_status = document.createElement('td');
            td_status.innerText = game.status;
            tr.append(td_status);

            let td_winner = document.createElement('td');
            td_winner.innerText = game.winner;
            tr.append(td_winner);

            let td_details = document.createElement('td');
            td_details.innerText = game.details;
            tr.append(td_details);

            let td_link = document.createElement('td');
            td_link.className= 'text-center';
            let link = document.createElement('a');
            link.className = 'text-decoration-none link-dark'
            switch (game.status) {
                case 'ended':
                case 'running':
                    link.href = `/game?room=${game.name}&room_id=${game.id}`;
                    break;
                case 'created':
                    link.href = `/game_room?room=${game.name}&room_id=${game.id}`;
                    break;
                default:
                    link.href = `#`;
                    break;
            }
            link.innerText = '➥';
            td_link.append(link);
            tr.append(td_link);
            div_table_body.append(tr);
        }
    }

    function drawStat(games_total, games_won) {
        let span_total = document.getElementById('games-total');
        let span_won = document.getElementById('games-won');
        span_total.innerText = games_total;
        span_won.innerText = games_won;
    }
});