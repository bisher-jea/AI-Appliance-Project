import { createClient } from
    "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

const supabaseUrl = "https://qhqbzayejaqyvkylqrwm.supabase.co";
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFocWJ6YXllamFxeXZreWxxcndtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQwMjYxMjQsImV4cCI6MjA5OTYwMjEyNH0.flsc3asxZpoWproDenaby1epHDBM2TCCWKSciQCihl0"; 
// both url and anon key can be in frontend, serivce key cannot

const loginForm =
    document.getElementById("loginForm");

const loginError =
    document.getElementById("loginError");

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    loginError.textContent = "";

    const email =
        document.getElementById("email").value.trim();

    const password =
        document.getElementById("password").value;

    try {
        const { data, error } =
            await supabase.auth.signInWithPassword({
                email,
                password,
            });

        if (error) {
            console.error("Supabase login error:", error);

            loginError.textContent =
                error.message;

            return;
        }

        if (!data.session) {
            loginError.textContent =
                "Login succeeded, but no session was created.";

            return;
        }

        console.log("Login successful:", data.user);

        window.location.href =
            "./admin_dashboard.html";
    } catch (error) {
        console.error("Unexpected login error:", error);

        loginError.textContent =
            "Unable to connect to the login service.";
    }
});