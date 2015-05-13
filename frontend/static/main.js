
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
var trial = 3;
const k6_trials = [3,6,7,8];

function reload() {
    var url = "/api/downloads?trial_id=3";
    if (trial == 4)
        url = "/api/downloads?trial_id=4";
    if (trial == 6)
        url = "/api/downloads?trial_id=6";
    $.getJSON(url, function(data) {
        if (k6_trials.indexOf(trial) != -1) {
            chartOptions.xAxis.title.text = "k";
            chartOptions.series = [{name: "1MB", data: []},
                                   {name: "10MB", data: []},
                                   {name: "100MB", data: []}
                                  ];
        } else {
            chartOptions.xAxis.title.text = "read size";
            chartOptions.series = [{name: "1MB k=1", data: []},
                                   {name: "1MB k=3", data: []},
                                   {name: "1MB k=6", data: []},
                                   {name: "1MB k=30", data: []},
                                   {name: "1MB k=60", data: []},
                                   {name: "10MB k=1", data: []},
                                   {name: "10MB k=3", data: []},
                                   {name: "10MB k=6", data: []},
                                   {name: "10MB k=30", data: []},
                                   {name: "10MB k=60", data: []}
                                  ];
        }
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
            var x, pushto;
            if (k6_trials.indexOf(trial) != -1) {
                x = p.k;
                if (p.filesize == 1*MB)
                    pushto = 0;
                if (p.filesize == 10*MB)
                    pushto = 1;
                if (p.filesize == 100*MB)
                    pushto = 2;
                s[pushto].data.push([x, value]);
            } else {
                x = p.readsize;
                if (p.k == 1)
                    pushto = 0;
                if (p.k == 3)
                    pushto = 1;
                if (p.k == 6)
                    pushto = 2;
                if (p.k == 30)
                    pushto = 3;
                if (p.k == 60)
                    pushto = 4;
                if (p.filesize == 10*MB)
                    pushto += 5;
                s[pushto].data.push([x, value]);
            }
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

    $("#trial-3").on("click", function() { trial = 3; reload(); });
    $("#trial-4").on("click", function() { trial = 4; reload(); });
    $("#trial-6").on("click", function() { trial = 6; reload(); });
    $("#trial-7").on("click", function() { trial = 7; reload(); });
    $("#trial-8").on("click", function() { trial = 8; reload(); });
});
