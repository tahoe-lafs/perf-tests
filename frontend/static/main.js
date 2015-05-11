
var chartOptions = {
    chart: {
        renderTo: "container",
        type: 'scatter',
        zoomType: "x"

    },
    title: {
        text: 'Download Speed'
    },
    xAxis: {
        title: { text: "k" }
    },
    yAxis: {
        title: {
            text: 'bytes per second'
        },
        min: 0
    },
    series: [{}]
    };

$(function () {
    Highcharts.setOptions({
    });
    $.getJSON("/api/downloads?trial_id=2", function(data) {
        chartOptions.series = [{name: "1MB", data: []},
                               {name: "10MB", data: []},
                               {name: "100MB", data: []}];
                          
        var s = chartOptions.series;
        const MB = 1000*1000;
        data.perfs.forEach(function(p) {
            // .filesize, .k, .download_time
            var speed = p.filesize / p.download_time;
            if (p.filesize == 1*MB)
                s[0].data.push([p.k, speed]);
            if (p.filesize == 10*MB)
                s[1].data.push([p.k, speed]);
            if (p.filesize == 100*MB)
                s[2].data.push([p.k, speed]);
        });
        var chart = new Highcharts.Chart(chartOptions);
    });
});
