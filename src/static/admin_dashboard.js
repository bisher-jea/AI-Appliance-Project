import { createClient } from
    "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

const SUPABASE_URL =
    "https://qhqbzayejaqyvkylqrwm.supabase.co";

const SUPABASE_ANON_KEY =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFocWJ6YXllamFxeXZreWxxcndtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQwMjYxMjQsImV4cCI6MjA5OTYwMjEyNH0.flsc3asxZpoWproDenaby1epHDBM2TCCWKSciQCihl0";

const API_URL =
    "https://ai-appliance-project.onrender.com";

const supabase = createClient(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
);

async function loadDashboard() {
    try {
        const {
            data: { session },
            error: sessionError,
        } = await supabase.auth.getSession();

        if (sessionError) {
            console.error(
                "Unable to retrieve session:",
                sessionError
            );

            window.location.href = "./admin_login.html";
            return;
        }

        if (!session) {
            window.location.href = "./admin_login.html";
            return;
        }

        // temp test endpt
        const response = await fetch(
            "https://ai-appliance-project.onrender.com/admin/test",
            {
                headers: {
                    Authorization: `Bearer ${session.access_token}`,
                },
            }
        );
        const result = await response.json();
        console.log(result);

        /*const response = await fetch(
            `${API_URL}/admin/submissions`,
            {
                method: "GET",
                headers: {
                    Authorization:
                        `Bearer ${session.access_token}`,
                    "Content-Type": "application/json",
                },
            }
        );*/
        if (
            response.status === 401 ||
            response.status === 403
        ) {
            await supabase.auth.signOut();
            window.location.href = "./admin_login.html";
            return;
        }

        if (!response.ok) {
            const errorMessage = await response.text();

            throw new Error(
                `Unable to load dashboard: ${errorMessage}`
            );
        }

        const submissions = await response.json();

        displaySubmissions(submissions);
    } catch (error) {
        console.error(error);

        const errorElement =
            document.getElementById("dashboardError");

        if (errorElement) {
            errorElement.textContent =
                "Unable to load dashboard data. Please try again.";
        }
    }
}

function displaySubmissions(submissions) {
    const tableBody =
        document.getElementById("submissionTableBody");

    if (!tableBody) {
        console.error(
            "Could not find submissionTableBody."
        );
        return;
    }

    tableBody.innerHTML = "";

    if (submissions.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8">
                    No submissions found.
                </td>
            </tr>
        `;
        return;
    }

    submissions.forEach((submission) => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${submission.address ?? "N/A"}</td>
            <td>${submission.appliance_type ?? "N/A"}</td>
            <td>${submission.brand ?? "N/A"}</td>
            <td>${submission.model_number ?? "N/A"}</td>
            <td>${submission.serial_number ?? "N/A"}</td>
            <td>${submission.age ?? "N/A"}</td>
            <td>
                ${submission.replacement_recommendation ?? "Review"}
            </td>
            <td>
                <button
                    type="button"
                    class="action-btn"
                    data-id="${submission.id}"
                >
                    Review
                </button>
            </td>
        `;

        tableBody.appendChild(row);
    });
}

async function logout() {
    const { error } = await supabase.auth.signOut();

    if (error) {
        console.error("Logout failed:", error);
        return;
    }

    window.location.href = "./admin_login.html";
}

const logoutButton =
    document.getElementById("logoutButton");

if (logoutButton) {
    logoutButton.addEventListener("click", logout);
}

loadDashboard();