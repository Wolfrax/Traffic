/**
 * Created by mm on 15/08/15.
 */

function newSerie(s, par) {
    // Return a new serie from s, normalize vs first element
    var r = [], e = [];
    var f = s[0][par];

    for (var i = 0; i < s.length; i++) {
        e = [s[i]['Time'], (s[i][par] - f)];
        r.push(e);
    }
    return r;
}

function sumSeries(s1, s2) {
    // s1 + s2, assuming equal size, time at index zero and assumed equal between s1 and s2
    var r = [], e = [];
    for (var i = 0; i < s1.length; i++) {
        e = [s1[i][0], s1[i][1] + s2[i][1]];
        r.push(e);
    }
    return r;
}

function newSerieNoAcc(s) {
    // Return a new serie with that is not accumulating from s
    var r = [], e;

    e = [s[0][0], s[0][1]];
    r.push(e);

    for (var i = 1; i < s.length; i++) {
        e = [s[i][0], s[i][1] - s[i - 1][1]];
        r.push(e);
    }
    return r;
}

function getVolElem(v) {
    if (v > 1020 * 1024)
      return ["GB", v / (1024 * 1024)];

    if (v > 1024)
      return ["MB", v / 1024];

    return ["kB", v];
}

function scale(str, s) {
    // Scale series by str
    var i;

    if (str == "GB") {
        for (i = 1; i < s.length; i++) {
            s[i][1] = s[i][1] / (1024 * 1024);
        }
        return s;
    }
    else if (str == "MB") {
        for (i = 1; i < s.length; i++) {
            s[i][1] = s[i][1] / 1024;
        }
        return s;
    }
    else
      return s;
}

function getMax(s) {
    // Return max value from s, last element
    return s[s.length - 1][1];
}

function scaleVal(str, v) {
    if (str == "GB") {
        return v;
    }
    else if (str == "MB")
      return v * 1024;
    else // kB
      return v * 1024 * 1024;
}

function labelFormatter(label, series) {
    return "<div style='font-size:12pt; text-align:center; padding:2px; color:black;'>" + label + "<br/>" + Math.round(series.percent) + "%</div>";
}

function plotTraffic(series) {
    var up, down, tot, sum;
    var upNoAcc, downNoAcc;
    var max_up, max_down;
    var upVolStr, downVolStr, totVolStr;
    var th; // threshold
    var fromDate, toDate, noOfDays, aveSum;
    var dayStr;

    up = newSerie(series, 'UplinkVolume');
    down = newSerie(series, 'DownlinkVolume');
    tot = sumSeries(up, down);

    max_up = getMax(up);
    upVolStr = getVolElem(max_up);

    max_down = getMax(down);
    downVolStr = getVolElem(max_down);

    totVolStr = getVolElem(max_up + max_down);

    up = scale(totVolStr[0], up);
    down = scale(totVolStr[0], down);
    tot = scale(totVolStr[0], tot);
    th = scaleVal(totVolStr[0], 40); // threshold is 40 GB, convert to current scale

    $.plot($("#graph1"),
            [ {data: up,
                  yaxis: 1,
                  lines: {show: true, fill: false, steps: true},
                  label: "Uplink volume (" + upVolStr[1].toFixed(0) + " "+ upVolStr[0] + ")"},
              {data: down,
                  yaxis: 1,
                  lines: {show: true, fill: false, steps: true},
                  label: "Downlink volume (" + downVolStr[1].toFixed(0) + " " + downVolStr[0] + ")"},
              {data: tot,
                  yaxis: 1,
                  lines: {show: true, fill: false, steps: true},
                  label: "Total volume (" + totVolStr[1].toFixed(0) + " " + totVolStr[0] +  ")"}
            ],
            { legend: {position: "nw"},
              xaxis:  {mode: "time", timezone: "browser"},
              yaxes:  [ {min: 0} ]
            });

    upNoAcc = newSerieNoAcc(up);
    downNoAcc = newSerieNoAcc(down);

    $.plot($("#graph2"),
            [ {data: upNoAcc,
                  yaxis: 1,
                  lines: {show: true, fill: true, steps: true},
                  label: "Uplink volume (" + upVolStr[0] + ")" },
              {data: downNoAcc,
                  yaxis: 1,
                  lines: {show: true, fill: true, steps: true},
                  label: "Downlink volume (" + downVolStr[0] + ")"}
            ],
            {legend: {position: "nw"},
             xaxis: {mode: "time", timezone: "browser"},
             yaxes: [{min: 0}]}
    );

    $.plot($("#pie1"),
            [ {data: max_up,
                  label: "Uplink" },
              {data: max_down,
                  label: "Downlink"}
            ],
           {series: {pie: {show: true, radius: 1, label: {show: true, radius: 2 / 3, formatter: labelFormatter}}},
           legend: {show: false}}
    );

    sum = getVolElem(max_up + max_down);

    $.plot($("#pie2"),
            [ {data: sum[1],
                  label: "Consumed" },
              {data: th - sum[1],
                  label: "Left"}
            ],
           {series: {pie: {show: true, radius: 1, label: {show: true, radius: 2 / 3, formatter: labelFormatter}}},
           legend: {show: false}}
    );

    fromDate  = new Date($("#dateFrom").val()).setHours(0);
    toDate = new Date($("#dateTo").val()).setHours(24);

    dayStr = " days ";
    noOfDays = (toDate - fromDate) / (1000 * 60 * 60 * 24);
    if (noOfDays <= 1) {
        noOfDays = 1; // toDate == fromDate
        dayStr = " day ";
    }

    aveSum = getMax(tot) / noOfDays;
    $("#trafficData").text(" (" + noOfDays.toFixed(0) + dayStr + aveSum.toFixed(1) + " " + totVolStr[0] + "/day)");

}

function Router() {
    // router object
    var firstUplinkVal = 0, firstDownlinkVal = 0;
    var upSum = 0, downSum = 0;
    var up = [], down = [];
    var upRate = [], downRate = [];
    var period = (10 * 60)/ 2; // 10 minutes in sec, sample rate every 2nd sec

    this.volume = function(time, upVal, downVal) {
        if (firstUplinkVal == 0) {
            firstUplinkVal = upVal;
        }

        upVal -= firstUplinkVal;

        if (firstDownlinkVal == 0) {
            firstDownlinkVal = downVal;
        }

        downVal -= firstDownlinkVal;

        up.push([time, upVal]);
        down.push([time, downVal]);
        upSum   += upVal;
        downSum += downVal;

        if (up.length > period) {
            firstUplinkVal = 0;
            firstDownlinkVal = 0;
            upSum -= up[0];
            downSum -= down[0];

            up.shift();
            down.shift();
        }

    };

    this.rate = function(time, upVal, downVal) {
        upRate.push([time, upVal]);
        downRate.push([time, downVal]);

        if (upRate.length > period) {
            upRate.shift();
            downRate.shift();
        }

    };

    this.getUpVolume = function() {
        return up;
    };

    this.getDownVolume = function() {
        return down;
    };

    this.getUpRate = function() {
        return upRate;
    };

    this.getDownRate = function() {
        return downRate;
    };

    this.getUpSum = function() {
        return upSum;
    };

    this.getDownSum = function() {
        return downSum;
    };

    this.getSumStr = function(str) {
        var val;

        if (str == 'up') {
            val = upSum;
        }
        else {
            val = downSum;
        }

        if (val > (1024 * 1024)) {
            val /= (1024 * 1024);
            return val.toFixed(1) + " GB";
        }
        else if (val > 1024) {
            val /= 1024;
            return val.toFixed(1) + " MB";
        }
        else {
            return val.toFixed(1) + " kB";
        }
    };

    this.scaleRate2Str = function(val) {
         if (val > (1000 * 1000)) {
            val /= (1000 * 1000);
            return val.toFixed(1) + " GB/s";
        }
        else if (val > 1000) {
            val /= 1000;
            return val.toFixed(1) + " MB/s";
        }
        else {
            return val.toFixed(1) + " kb/s";
        }

    };
}

function plotRealTime(d, r) {
    var g_up = $('#gauge-up');
    var g_down = $('#gauge-down');
    var gaugeOptions = {

        chart: {
            type: 'solidgauge'
        },

        title: null,

        pane: {
            center: ['50%', '85%'],
            size: '140%',
            startAngle: -90,
            endAngle: 90,
            background: {
                backgroundColor: (Highcharts.theme && Highcharts.theme.background2) || '#EEE',
                innerRadius: '60%',
                outerRadius: '100%',
                shape: 'arc'
            }
        },

        tooltip: {
            enabled: false
        },

        // the value axis
        yAxis: {
            stops: [
                [0.1, '#55BF3B'], // green
                [0.5, '#DDDF0D'], // yellow
                [0.9, '#DF5353'] // red
            ],
            lineWidth: 0,
            minorTickInterval: null,
            tickPixelInterval: 400,
            tickWidth: 0,
            title: {
                y: -70
            },
            labels: {
                y: 16
            }
        },

        plotOptions: {
            solidgauge: {
                dataLabels: {
                    y: 5,
                    borderWidth: 0,
                    useHTML: true
                }
            }
        }
    };

    r.volume(d.time, d['uplink'], d['downlink']);
    r.rate(d.time, d['uplink rate'], d['downlink rate']);

    $.plot($("#graph1"), [
            {data: r.getUpVolume(),
                lines: {show: true, fill: true},
                label: "Uplink volume (" + r.getSumStr('up') + ")"},
            {data: r.getDownVolume(),
                lines: {show: true, fill: true},
                label: "Downlink volume (" + r.getSumStr('down') + ")"},
            {data: r.getUpRate(),
                yaxis: 2,
                label: "Uplink rate (" + r.scaleRate2Str(d['uplink rate']) + ")"},
            {data: r.getDownRate(),
                yaxis: 2,
                label: "Downlink rate (" + r.scaleRate2Str(d['downlink rate']) + ")"}
        ],
        {legend: {position: "nw"},
            xaxis: {mode: "time", timezone: "browser"},
            yaxes: [{min: 0 }, {position: "right", min: 0}]});

    $.plot($("#pie1"),
        [{data: r.getUpSum(),
            label: "Volume up"},
         {data: r.getDownSum(),
             label: "Volume down"}
        ],
        {series: {pie: {show: true, radius: 1, label: {show: true, radius: 2 / 3, formatter: labelFormatter}}},
            legend: {show: false}}
    );

    $.plot($("#pie2"),
        [{data: d['uplink rate'],
            label: "Rate up"},
         {data: d['downlink rate'],
             label: "Rate down"}
        ],
        {series: {pie: {show: true, radius: 1, label: {show: true, radius: 2 / 3, formatter: labelFormatter}}},
            legend: {show: false}}
    );

    // The uplink speed gauge
    g_up.highcharts(Highcharts.merge(gaugeOptions, {
        yAxis: {
            min: 0,
            max: 2000,
            title: {
                text: 'Uplink'
            }
        },

        credits: {
            enabled: false
        },

        series: [{
            name: 'Speed up',
            data: [80],
            dataLabels: {
                format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                    ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y}</span><br/>' +
                       '<span style="font-size:12px;color:silver">kb/s</span></div>'
            },
            tooltip: {
                valueSuffix: ' kb/s'
            }
        }]

    }));

    // The downlink speed gauge
    g_down.highcharts(Highcharts.merge(gaugeOptions, {
        yAxis: {
            min: 0,
            max: 2000,
            title: {
                text: 'Downlink'
            }
        },

        credits: {
            enabled: false
        },

        series: [{
            name: 'Speed down',
            data: [80],
            dataLabels: {
                format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                    ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y}</span><br/>' +
                       '<span style="font-size:12px;color:silver">kb/s</span></div>'
            },
            tooltip: {
                valueSuffix: ' kb/s'
            }
        }]

    }));

    g_up.highcharts().series[0].points[0].update(d['uplink rate']);
    g_down.highcharts().series[0].points[0].update(d['downlink rate']);

}