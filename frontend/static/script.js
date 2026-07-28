
const applianceCount =
    document.getElementById("applianceCount");

const applianceContainer =
    document.getElementById("applianceContainer");

const machineForm =
    document.getElementById("machineForm");

const applianceType =
    document.getElementById("applianceType");


function createSystemQuestions() {
    const count = Number(
        applianceCount.value
    );

    const type = applianceType.value;

    applianceContainer.innerHTML = "";

    if (!count || count < 1 || !type) {
        return;
    }

    for (let i = 1; i <= count; i++) {
        const systemDiv =
            document.createElement("div");

        systemDiv.className = "system-card";

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
                <hr>
            `;
        }

        if (type === "Water Heater") {
            systemDiv.innerHTML = `
                <h2>Water Heater ${i}</h2>

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
                <hr>
            `;
        }

        applianceContainer.appendChild(
            systemDiv
        );
    }
}


applianceCount.addEventListener(
    "input",
    createSystemQuestions
);

applianceType.addEventListener(
    "change",
    createSystemQuestions
);


machineForm.addEventListener(
    "submit",
    function (event) {
        const type = applianceType.value;

        if (type === "HVAC") {
            machineForm.action =
                "/appliances/hvac/submit";
        } else if (type === "Water Heater") {
            machineForm.action =
                "/appliances/water-heaters/submit";
        } else {
            event.preventDefault();

            alert(
                "Please select an appliance type."
            );

            return;
        }

        machineForm.method = "POST";
        machineForm.enctype =
            "multipart/form-data";

        const submitButton =
            machineForm.querySelector(
                'button[type="submit"], '
                + 'input[type="submit"]'
            );

        if (submitButton) {
            submitButton.disabled = true;
        }

        /*
         * Do not call event.preventDefault().
         *
         * The browser submits the form directly to
         * FastAPI and follows the RedirectResponse
         * returned by the backend.
         *
         * That redirect should include both address
         * and batch_id in the report URL.
         */
    }
);
