
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

var mode = "time";

function reload() {
    $.getJSON("/api/downloads?trial_id=3", function(data) {
        chartOptions.series = [{name: "1MB", data: []},
                               {name: "10MB", data: []},
                               {name: "100MB", data: []}];
        if (mode == "speed") {
            chartOptions.title = "Download Speed";
            chartOptions.yAxis.title.text = "bytes per second";
        } else {
            chartOptions.title = "Download Time";
            chartOptions.yAxis.title.text = "seconds";
        }
                          
        var s = chartOptions.series;
        const MB = 1000*1000;
        data.perfs.forEach(function(p) {
            // .filesize, .k, .download_time
            var value;
            if (mode == "speed")
                value = p.filesize / p.download_time;
            else
                value = p.download_time;
            if (p.filesize == 1*MB)
                s[0].data.push([p.k, value]);
            if (p.filesize == 10*MB)
                s[1].data.push([p.k, value]);
            if (p.filesize == 100*MB)
                s[2].data.push([p.k, value]);
        });
        var chart = new Highcharts.Chart(chartOptions);
    });
}

$(function () {
    reload();
    $("#mode-time").on("click", function() {
        mode = "time";
        reload();
    });
    $("#mode-speed").on("click", function() {
        mode = "speed";
        reload();
    });
});
