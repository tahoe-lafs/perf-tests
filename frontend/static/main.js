$(function () {
    Highcharts.setOptions({
    });
    var options = {
        chart: {
            renderTo: "container",
            type: 'bar'
        },
        title: {
            text: 'Download Time'
        },
        xAxis: {
            //categories: ['Apples', 'Bananas', 'Oranges']
            title: { text: "k" }
        },
        yAxis: {
            title: {
                text: 'seconds'
            }
        },
        NOTseries: [{
            name: 'Jane',
            data: [1, 0, 4]
        }, {
            name: 'John',
            data: [5, 7, 3]
        }],
        series: [{}]
    };
    $.getJSON("/api/downloads?trial_id=2", function(data) {
        options.series[0].data = data.perfs;
        // .filesize, .k, .download_time
        var chart = new Highcharts.Chart(options);
    });
});
