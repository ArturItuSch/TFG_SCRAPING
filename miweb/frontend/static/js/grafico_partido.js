let chartInstancia = null;
let graficoCargado = false;

function mostrarVista(vista) {
  document.getElementById('vista-tarjetas').style.display = (vista === 'tarjetas') ? 'block' : 'none';
  document.getElementById('vista-grafico').style.display = (vista === 'grafico') ? 'block' : 'none';

  if (vista === 'grafico' && !graficoCargado) {
    mostrarGrafico('gold');
    graficoCargado = true;
  }
}

function mostrarGrafico(tipo) {
  const ctx = document.getElementById('graficoEstadisticas').getContext('2d');

  if (chartInstancia) {
    chartInstancia.destroy();
  }

  chartInstancia = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [datasetsPorTipo[tipo]]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true },
        tooltip: { enabled: true }
      },
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: datasetsPorTipo[tipo].label
          }
        },
        y: {
          ticks: { color: '#fff' }
        }
      }
    }
  });
}