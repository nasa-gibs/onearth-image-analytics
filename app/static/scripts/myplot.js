function loadPlot() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
       document.getElementById("plot").innerHTML = this.responseText;
      }
      $("#plot").find("script").each(function(){
        eval($(this).text());
      });
    };
    xhttp.open("GET", "getplot", true);
    xhttp.send();
  }