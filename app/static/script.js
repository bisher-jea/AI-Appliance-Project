const systemCount = document.getElementById("systemCount");
const systemsContainer = document.getElementById("systemsContainer");
const machineForm = document.getElementById("machineForm");
const applianceType = document.getElementById("applianceType");

function createSystemQuestions() {
    const count = Number(systemCount.value);
    const type = applianceType.value;

    systemsContainer.innerHTML = "";
    
    // dynamic questions: shows the following set of questions x amt of times where x is the response to the previous question
    if (!count || count < 1 || !type) {
        return;
    }

    for (let i = 1; i <= count; i++) {
        const systemDiv = document.createElement("div");
        systemDiv.className = "system-card";

        // if HVAC selected, prompt for indoor and outdoor nameplate
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
                    multiple accept="image/*"
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
                    multiple accept="image/*"
                    required
                >

                <br><br>
                <hr>
            `;
        }

        systemsContainer.appendChild(systemDiv);
    }
}

systemCount.addEventListener("input", createSystemQuestions);
applianceType.addEventListener("change", createSystemQuestions);

machineForm.addEventListener("submit", function(event) {
    event.preventDefault();

    const formData = new FormData(machineForm);

    console.log("Submitted Form Data:");

    for (const [key, value] of formData.entries()) {
        console.log(key, value);
    }

    alert("Form submitted successfully!");
});