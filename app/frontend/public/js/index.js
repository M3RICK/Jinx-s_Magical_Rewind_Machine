async function sendForm(e)
{
    e.preventDefault();
    const data = {
        username: document.getElementById("username").value,
        hashtag: document.getElementById("hashtag").value,
        server: document.getElementById("server").value,
    };

    const res = await fetch("/api/rewind", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data),
    });

    const result = await res.json();
    alert(`Rewind received! ${result.message}`);
}
