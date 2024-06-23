// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';
function number_format(number, decimals, dec_point, thousands_sep) {
  // *     example: number_format(1234.56, 2, ',', ' ');
  // *     return: '1 234,56'

  number = (number + '').replace(',', '').replace(' ', '');
  var n = !isFinite(+number) ? 0 : +number,
    prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
    sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
    dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
    s = '',
    toFixedFix = function(n, prec) {
      var k = Math.pow(10, prec);
      return '' + Math.round(n * k) / k;
    };
  // Fix for IE parseFloat(0.55).toFixed(0) = 0;
  s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
  if (s[0].length > 3) {
    s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
  }
  if ((s[1] || '').length < prec) {
    s[1] = s[1] || '';
    s[1] += new Array(prec - s[1].length + 1).join('0');
  }
  return s.join(dec);
}

// Area Chart Example
var ctx = document.getElementById("myAreaChart");
var products = [
    ["MORNIF MEAT", "NASOYA VEGET", "GG OATMILK", "PILLSBURY", "GG STARBUCKS", "GG FRUIT", "GG FRUIT", "TOFURKY MEAT", "TAZO", "ANNIE'S", "SBR", "SOUP", "SILK", "MI OLIVE PKL", "BISCOFF.8OZ", "GG GRANOLA", "HH KINARA", "NATURE’S", "ANNIES FRFT"],
    [1100, 1200, 900, 850, 800, 825, 750, 760, 760, 760, 740, 750, 720, 700, 680, 650, 655, 660, 640, 740, 750, 720, 700, 680, 650, 655, 660, 640, 740, 750, 720, 700, 680, 650, 655, 660, 640,740, 750, 720, 700, 680, 650, 655, 660, 640,740, 750, 720, 700, 680, 650, 655, 660, 640],
    ["Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food", "Food"]
]

var myLineChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: ["Jan", "", "", "", "Feb", "", "", "", "Mar", "", "", "", "Apr", "", "", "", "May", "", "", "", "Jun", "", "", "", "Jul", "", "", "", "Aug", "", "", "", "Sep", "", "", "", "Oct", "", "", "", "Nov", "", "", "", "Dec"],
    datasets: [{
      label: "Earnings",
      lineTension: 0.3,
      backgroundColor: "rgba(78, 115, 223, 0.05)",
      borderColor: "rgba(78, 115, 223, 1)",
      pointRadius: 3,
      pointBackgroundColor: "rgba(78, 115, 223, 1)",
      pointBorderColor: "rgba(78, 115, 223, 1)",
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
      pointHoverBorderColor: "rgba(78, 115, 223, 1)",
      pointHitRadius: 10,
      pointBorderWidth: 0,
      data: products[1]
    }],
  },
  options: {
    maintainAspectRatio: false,
    layout: {
      padding: {
        left: 10,
        right: 25,
        top: 25,
        bottom: 0
      }
    },
    scales: {
      xAxes: [{
        time: {
          unit: 'week'
        },
        gridLines: {
          display: false,
          drawBorder: false
        },
        ticks: {
          maxTicksLimit: 52,
          callback: function(value, index, values) {
            // Display only the labels corresponding to the start of each month
            if (value === "Jan" || value === "Feb" || value === "Mar" || value === "Apr" || value === "May" ||
                value === "Jun" || value === "Jul" || value === "Aug" || value === "Sep" || value === "Oct" ||
                value === "Nov" || value === "Dec") {
              return value;
            }
            return '';
          }
        }
      }],
      yAxes: [{
        ticks: {
          maxTicksLimit: 5,
          padding: 10,
          // Include a dollar sign in the ticks
          callback: function(value, index, values) {
            return number_format(value) + 'kg ';
          }
        },
        gridLines: {
          color: "rgb(234, 236, 244)",
          zeroLineColor: "rgb(234, 236, 244)",
          drawBorder: false,
          borderDash: [2],
          zeroLineBorderDash: [2]
        }
      }],
    },
    legend: {
      display: false
    },
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      titleMarginBottom: 10,
      titleFontColor: '#6e707e',
      titleFontSize: 14,
      borderColor: '#dddfeb',
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      intersect: false,
      mode: 'index',
      caretPadding: 10,
      callbacks: {
        label: function(tooltipItem, chart) {
          var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
          return datasetLabel + ': Carbon ' + number_format(tooltipItem.yLabel);
        }
      }
    }
  }
});
