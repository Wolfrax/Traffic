<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
    "http://www.w3.org/TR/html4/strict.dtd"
    >
<html lang="en">
<head>
    <title>Router traffic monitor</title>
    <script type="text/JavaScript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js"></script>
    <script language="javascript" type="text/javascript" src="../js/jquery/jquery.flot.js"></script>
    <script language="javascript" type="text/javascript" src="../js/jquery/jquery-ui-1.10.0.custom.js"></script>
    <link rel="stylesheet" href="../js/jquery/css/ui-lightness/jquery-ui-1.10.0.custom.css" />
</head>
<body>
    <!-- Insert your content here -->
    <h2>ABC</h2>
    <div id="graph1" style="width:1000px;height:500px"></div>
        
    <script type="text/javascript">      
    $(function () {
                
      function updateTraffic() {
	      $.ajax({
	      url: "/cgi-bin/Traffic.py",
	      method: 'GET',
	      data: {Start: 'abc',
		     Stop : 'def'},
	      dataType: 'json',
	      cache: false,
	      }).done(function(series) {
                $.plot($("#graph1"), [{data: series[2], label: "Traffic", lines: {fill: true}, yaxis: 3}]);
                }); // ajax
	      
	  setTimeout(updateTraffic, 1000); // 1 second
      } // updateTraffic
      
      updateTraffic();

    });
    </script>
</body>
</html>
