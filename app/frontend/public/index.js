async function sendForm(e) {
    e.preventDefault();
    
    const loadingScreen = document.getElementById('loadingScreen');
    const loadingBar = document.getElementById('loadingBar');
    const loadingPercent = document.getElementById('loadingPercent');
    
    loadingScreen.classList.remove('hidden');
    
    let progress = 0;
    const loadingInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        loadingBar.style.width = progress + '%';
        loadingPercent.textContent = Math.floor(progress) + '%';
    }, 200);
    
    const data = {
        username: document.getElementById("username").value,
        hashtag: document.getElementById("hashtag").value,
        server: document.getElementById("server").value,
    };
    
    try {
        const res = await fetch("http://localhost:5000/api/rewind", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data),
        });

        const result = await res.json();

        clearInterval(loadingInterval);
        loadingBar.style.width = '100%';
        loadingPercent.textContent = '100%';
        
        setTimeout(() => {
            loadingScreen.classList.add('hidden');

            if (res.ok) {
                alert(`Rewind received! ${result.message}`);
            } else {
                alert(`Error: ${result.message || 'An error occurred'}`);
            }
        }, 500);

    } catch (error) {
        clearInterval(loadingInterval);
        loadingScreen.classList.add('hidden');
        alert(`Connection error: ${error.message}`);
    }
}
