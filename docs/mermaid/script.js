document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded')
    const fileInput = document.getElementById('fileInput');
    const viewButton = document.getElementById('viewButton');
    const mermaidContainer = document.getElementById('mermaidContainer');
  
    viewButton.addEventListener('click', function() {
      const file = fileInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
          const content = e.target.result;
          mermaidContainer.innerHTML = content;
          mermaid.init(undefined, mermaidContainer);
        };
        reader.readAsText(file);
      }
    });
  });