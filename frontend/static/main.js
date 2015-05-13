
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

var qs = (function(a) {
    if (a == "") return {};
    var b = {};
    for (var i = 0; i < a.length; ++i)
    {
        var p=a[i].split('=', 2);
        if (p.length == 1)
            b[p[0]] = "";
        else
            b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, " "));
    }
    return b;
})(window.location.search.substr(1).split('&'));

const MB = 1000*1000;
var mode = qs["mode"] || "time";
var trial = Number(qs["trial"] || 3);
const partial_old_trials = [4];
const partial_100MB_trials = [11];

var series_functions = {
    partial_old: function(p) {
        var pushto;
        if (p.k == 1) pushto = 0;
        if (p.k == 3) pushto = 1;
        if (p.k == 6) pushto = 2;
        if (p.k == 30) pushto = 3;
        if (p.k == 60) pushto = 4;
        if (p.filesize == 10*MB) pushto += 5;
        return pushto;
    },
    partial_100MB: function(p) {
        if (p.k == 1) return 0;
        if (p.k == 3) return 1;
        if (p.k == 6) return 2;
    },
    by_filesize: function(p) {
        if (p.filesize == 1*MB) return 0;
        if (p.filesize == 10*MB) return 1;
        if (p.filesize == 100*MB) return 2;
    }
};

function reload() {
    console.log("loading trial="+trial+" mode="+mode);
    var url = "/api/downloads?trial_id=" + trial;
    var seriesfunc;
    $.getJSON(url, function(data) {
        if (partial_old_trials.indexOf(trial) != -1) {
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
            seriesfunc = series_functions.partial_old;
        } else if (partial_100MB_trials.indexOf(trial) != -1) {
            chartOptions.xAxis.title.text = "read size";
            chartOptions.series = [{name: "100MB k=1", data: []},
                                   {name: "100MB k=3", data: []},
                                   {name: "100MB k=6", data: []},
                                  ];
            seriesfunc = series_functions.partial_100MB;
        } else {
            chartOptions.xAxis.title.text = "k";
            chartOptions.series = [{name: "1MB", data: []},
                                   {name: "10MB", data: []},
                                   {name: "100MB", data: []}
                                  ];
            seriesfunc = series_functions.by_filesize;
        }
        if (mode == "speed") {
            chartOptions.title = "Download Speed";
            chartOptions.yAxis.title.text = "bytes per second";
        } else {
            chartOptions.title = "Download Time";
            chartOptions.yAxis.title.text = "seconds";
        }

        var s = chartOptions.series;
        data.perfs.forEach(function(p) {
            // .filesize, .k, .download_time
            var value;
            if (mode == "speed")
                value = p.filesize / p.download_time;
            else
                value = p.download_time;
            var x;
            if (partial_old_trials.indexOf(trial) != -1 ||
                partial_100MB_trials.indexOf(trial) != -1) {
                x = p.readsize;
                chartOptions.xAxis.min = 0;
            } else {
                x = p.k;
                delete chartOptions.xAxis.min;
            }
            s[seriesfunc(p)].data.push([x, value]);
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
