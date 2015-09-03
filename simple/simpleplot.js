/**
 * Created by mm on 11/08/15.
 */
$(function simpleplot() {
    UplinkVolume = [];
    DownlinkVolume = [];
    UplinkRate = [];
    DownlinkRate = [];
    Id = 0;
    lastUpVol = 0;
    lastDownVol = 0;
    Period = 30 * 60; // 30 minutes expressed in seconds
    SampleRate = 2; // seconds
    PeriodLength = (Period / SampleRate).toFixed(0);
    firstUpVal = 0;
    firstDownVal = 0;

    function updateSimple() {
        $.ajax({
            url: "simple_web.py",
            method: 'GET',
            data: {sessionId: Id},
            dataType: 'json',
            cache: false
        }).done(function (series) {
            // {"downlink": 1107945322.0, "IP address": "78.78.162.49", "time": 1439318823000, "uplink rate": 2.0, "session id": 2124146035, "uplink": 325814586.0, "downlink rate": 7.0}

            Id = series["session id"];

            UpVol = new Array(2);
            UpVol[0] = series["time"];
            if (lastUpVol == 0)
                lastUpVol = series["uplink"];
            UpVol[1] = (series["uplink"] - lastUpVol);
            UplinkVolume.push(UpVol);
            if (UplinkVolume.length > PeriodLength)
                UplinkVolume.shift();
            lastUpVol = series["uplink"];
            upSum = 0;
            for (var ind = 0; ind < UplinkVolume.length; ind++) {
                upSum += UplinkVolume[ind][1];
            }

            DownVol = new Array(2);
            DownVol[0] = series["time"];
            if (lastDownVol == 0)
                lastDownVol = series["downlink"];
            DownVol[1] = (series["downlink"] - lastDownVol);
            DownlinkVolume.push(DownVol);
            if (DownlinkVolume.length > PeriodLength)
                DownlinkVolume.shift();
            lastDownVol = series["downlink"];
            downSum = 0;
            for (var ind = 0; ind < DownlinkVolume.length; ind++) {
                downSum += DownlinkVolume[ind][1];
            }

            UpRate = new Array(2);
            UpRate[0] = series["time"];
            UpRate[1] = series["uplink rate"];
            UplinkRate.push(UpRate);
            if (UplinkRate.length > PeriodLength)
                UplinkRate.shift();

            DownRate = new Array(2);
            DownRate[0] = series["time"];
            DownRate[1] = series["downlink rate"];
            DownlinkRate.push(DownRate);
            if (DownlinkRate.length > PeriodLength)
                DownlinkRate.shift();

            $.plot($("#graph1"), [
                        {data: UplinkVolume, lines: {show: true, fill: true}, label: "Uplink volume (" + (upSum / 1024).toFixed(1) + " kB)"},
                        {data: DownlinkVolume, lines: {show: true, fill: true}, label: "Downlink volume (" + (downSum / 1024).toFixed(1) + " kB)"},
                        {data: UplinkRate, yaxis: 2, label: "Uplink rate (" + UpRate[1] + " kbps)"},
                        {data: DownlinkRate, yaxis: 2, label: "Downlink rate (" + DownRate[1] + " kbps)"}
                    ],
                    {legend: {position: "nw"}, xaxis: {mode: "time"}, yaxes: [
                        {min: 0 },
                        { position: "right", min: 0}
                    ]});

        }); // ajax

        setTimeout(updateSimple, SampleRate * 1000); // seconds
    } // updateSimple

     updateSimple();

});