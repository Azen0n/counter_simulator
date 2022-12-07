$(document).ready(function () {
    document.getElementById('control_panel_button').addEventListener('click', function () {
        updateCounterSimulator();
    });

    document.getElementById('add_counter_button').addEventListener('click', function () {
        addCounter();
    });

    document.getElementById('change_number_of_counters_button').addEventListener('click',
        function () {
            changeNumberOfCounters();
        });

    let togglePauseBtn = document.getElementById('toggle_pause');
    togglePauseBtn.addEventListener('click', function () {
        togglePause();
    });

    function togglePause() {
        $.ajax({
            type: 'POST',
            url: `toggle_pause`,
            dataType: 'json',
            success: function (data) {
                if (data['is_on_pause']) {
                    togglePauseBtn.innerHTML = 'Продолжить';
                    console.log('Работа симулятора касс приостановлена.');
                } else {
                    togglePauseBtn.innerHTML = 'Приостановить';
                    console.log('Работа симулятора касс продолжается.');
                }
            },
        });
    }

    function addCounter() {
        $.ajax({
            type: 'POST',
            url: `create_counter`,
            dataType: 'json',
            success: function (data) {
                console.log(`Касса ${data['id']} создана`);
            },
        });
    }

    function changeNumberOfCounters() {
        let number_of_counters = $('#control_panel [name="number_of_counters"]')[0].value;
        $.ajax({
            type: 'POST',
            url: `change_number_of_counters`,
            data: {'number_of_counters': number_of_counters},
            dataType: 'json',
            success: function (data) {
                console.log(data);
                if (data['action'] === 'create') {
                    for (let counter of data['counters']) {
                        createCounter(counter);
                    }
                } else if (data['action'] === 'delete') {
                    for (let counter of data['counters']) {
                        $(`#${counter}`).remove();
                    }
                }
            },
        });
    }

    $('[id^="form"] [name="delete_counter_button"]').on('click', function () {
        let form = $(this).parents('form:first')[0];
        let counter_id = form.id.replace('form', '');
        deleteCounter(counter_id);
    });

    function deleteCounter(counter_id) {
        $.ajax({
            type: 'DELETE',
            url: `delete_counter/${counter_id}`,
            dataType: 'json',
            success: function (data) {
                let counter = $(`#${counter_id}`);
                counter.remove();
                console.log(`Касса ${counter_id} удалена`);
            },
        });
    }

    setTimeout(sendRequest, 1000);

    function sendRequest() {
        $.ajax({
            type: 'GET',
            url: 'fetch',
            dataType: 'json',
            success: function (data) {
                update(data);
            },
            complete: function (data) {
                setTimeout(sendRequest, 1000);
            }
        });
    }

    function update(data) {
        $('#wave_size').text(`${data['counter_simulator']['last_wave_size']}`);
        if (data['counter_simulator']['complainers'] > 0) {
            $('#complainers').text(`Ждут открытия касс: ${data['counter_simulator']['complainers']}`);
        } else {
            $('#complainers').text('');
        }
        for (let counter of data['counter_simulator']['counters']) {
            if ($(`#${counter['id']}`).length > 0) {
                $(`#${counter['id']} #queue_size`).text(counter['queue_size']);
                $(`#${counter['id']} #counter_id`).css('background', '');
                let total_service_time = counter['service_times'].reduce((a, b) => a + b, 0);
                let average_service_time = (total_service_time / counter['service_times'].length) || 0;
                $(`#${counter['id']} #average_service_time`).text(average_service_time.toFixed(2));
            } else {
                createCounter(counter);
            }
        }

        let minQueueSizeCounter = getMinQueueSize(data);
        let maxQueueSizeCounter = getMaxQueueSize(data);

        if (minQueueSizeCounter) {
            $(`#${minQueueSizeCounter['id']} #counter_id`).css('background', 'green');
        }
        if (maxQueueSizeCounter) {
            $(`#${maxQueueSizeCounter['id']} #counter_id`).css('background', 'red');
        }
    }

    function getMinQueueSize(data) {
        let counters = data['counter_simulator']['counters'];
        let min = counters[0];
        for (let counter of counters) {
            if (counter['queue_size'] < min['queue_size']) {
                min = counter;
            }
        }
        return min;
    }

    function getMaxQueueSize(data) {
        let counters = data['counter_simulator']['counters'];
        let max = counters[0];
        for (let counter of counters) {
            if (counter['queue_size'] > max['queue_size']) {
                max = counter;
            }
        }
        return max;
    }

    $('[id^="form"]').on('submit', function (e) {
        updateCounterWithAjax(e);
    });

    $('#control_panel_form').on('submit', function (e) {
        e.preventDefault();
    });

    function updateCounterWithAjax(e) {
        let form = e.target;
        let counter_id = form.id.replace('form', '');
        updateCounter(counter_id, form.min_time.value, form.max_time.value);
        e.preventDefault();
    }

    function updateCounter(counter_id, min_time, max_time) {
        $.ajax({
            type: 'POST',
            url: `update_counter/${counter_id}`,
            data: {
                'counter_id': counter_id,
                'min_time': min_time,
                'max_time': max_time
            },
            dataType: 'json',
            success: function (data) {
                if (!jQuery.isEmptyObject(data)) {
                    let counterForm = $(`#form${counter_id}`);
                    counterForm.min_time = min_time;
                    counterForm.max_time = max_time;
                    console.log(`Counter ${data.id} updated`)
                }
            },
        });
    }

    function updateCounterSimulator() {
        let wave_max_size = $('input[name="wave_max_size"]')[0].value;
        let wave_max_interval = $('input[name="wave_max_interval"]')[0].value;

        $.ajax({
            type: 'POST',
            url: 'update_counter_simulator',
            data: {
                'wave_max_size': wave_max_size,
                'wave_max_interval': wave_max_interval
            },
            dataType: 'json',
            success: function () {
                console.log('Counter Simulator parameters updated');
            }
        });
    }

    function createCounterComponent(counter) {
        let total_service_time = counter['service_times'].reduce((a, b) => a + b, 0);
        let average_service_time = (total_service_time / counter['service_times'].length) || 0;
        let div = document.createElement('div');
        div.id = `${counter.id}`;
        div.innerHTML = `
            <span id="counter_id">Касса ${counter.id}</span><br>
            Клиентов в очереди: <span id="queue_size">${counter.queue_size}</span><br>
            Среднее время обслуживания: <span id="average_service_time">${average_service_time.toFixed(2)}</span>
            <form action="/update_counter/${counter.id}"
                  method="post"
                  id="form${counter.id}">
                <label>Минимальное время обслуживания
                    <input name="min_time" type="number" value="${counter.min_time}" min="1" required>
                </label>
                <br>
                <label>Максимальное время обслуживания
                    <input name="max_time" type="number" value="${counter.max_time}" min="1" required>
                </label>
                <button type="submit">Изменить</button>
                <button type="button" name="delete_counter_button">Удалить</button>
            </form>
        `;
        return div;
    }

    function createCounter(counter) {
        let counters = document.getElementById('counters');
        let div = createCounterComponent(counter);
        counters.append(div);
        $(`[id="form${counter['id']}"] [name="delete_counter_button"]`).on('click', function () {
            let form = $(this).parents('form:first')[0];
            let counter_id = form.id.replace('form', '');
            deleteCounter(counter_id);
        });
        $(`[id="form${counter['id']}"]`).on('submit', function (e) {
            updateCounterWithAjax(e);
        });
    }
});