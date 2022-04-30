document.addEventListener('DOMContentLoaded', () => {
    const div_table_body = document.getElementById('history-table-body');

    let response = fetch(`./api/user_games`)
            .then(response => response.json())
            .then(response_json => {
                drawGames(response_json);
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
});