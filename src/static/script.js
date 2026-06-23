const applianceCount = document.getElementById("applianceCount");
const applianceContainer = document.getElementById("applianceContainer");
const machineForm = document.getElementById("machineForm");
const applianceType = document.getElementById("applianceType");

function createSystemQuestions() {
    const count = Number(applianceCount.value);
    const type = applianceType.value;

    applianceContainer.innerHTML = "";
    
    // dynamic questions: shows the following set of questions x amt of times where x is the response to the previous question
    if (!count || count < 1 || !type) {
        return;
    }

    for (let i = 1; i <= count; i++) {
        const systemDiv = document.createElement("div");
        systemDiv.className = "system-card";

        // if HVAC selected, prompt for nameplate
        if (type === "HVAC") {
            systemDiv.innerHTML = `
                <h2>HVAC System ${i}</h2>

                <label for="Nameplate${i}">
                    Upload System ${i} Nameplate:
                </label>
                <input 
                    type="file" 
                    id="Nameplate${i}" 
                    name="Nameplate${i}" 
                    accept="image/*"
                    required
                >

                <br><br>


                <br><br>
                <hr>
            `;
        }

        // if waterheater selected, only prompt for one nameplate photo
        if (type === "Water Heater") {
            systemDiv.innerHTML = `
                <h2>Water Heater ${i}</h2>

                <label for="waterHeaterNameplate${i}">
                    Upload System ${i} Nameplate:
                </label>
                <input 
                    type="file" 
                    id="waterHeaterNameplate${i}" 
                    name="waterHeaterNameplate${i}" 
                    accept="image/*"
                    required
                >

                <br><br>
                <hr>
            `;
        }

        applianceContainer.appendChild(systemDiv);
    }
}

applianceCount.addEventListener("input", createSystemQuestions);
applianceType.addEventListener("change", createSystemQuestions);

machineForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const formData = new FormData(machineForm);
    const type = applianceType.value;

    let submitUrl = "";

    if (type === "HVAC") {
        submitUrl = "/hvac/submit";
    } else if (type === "Water Heater") {
        submitUrl = "/water-heater/submit";
    } else {
        alert("Please select an appliance type.");
        return;
    }

    const response = await fetch(submitUrl, {
        method: "POST",
        body: formData,
        redirect: "follow"
    });

    if (response.redirected) {
        window.location.href = response.url;
        return;
    }

    if (!response.ok) {
        const errorText = await response.text();
        console.error(errorText);
        alert("Submission failed. Check the console or terminal.");
        return;
    }

    const result = await response.json();
    console.log(result);
});