const ctx = document.getElementById('myChart');
  fetch('/turnover')
  .then((response) => {
    return response.json();
  })
  .then((data) => {
    let d1 = [];
    let d2 = [];
    data.forEach(el => {
        d1.push(el[0])
        d2.push(el[1])
        });
    new Chart(ctx, {
    type: 'line',
    data: {
      labels: d1,
      datasets: [{
        label: 'Оборот',
        data: d2,
        borderWidth: 2,
        borderColor: '#FF6384',
        backgroundColor: '#FFB1C1',
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
  });