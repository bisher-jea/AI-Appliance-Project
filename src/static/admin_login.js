import { createClient } from
    "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

const supabaseUrl = "https://qhqbzayejaqyvkylqrwm.supabase.co";
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFocWJ6YXllamFxeXZreWxxcndtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQwMjYxMjQsImV4cCI6MjA5OTYwMjEyNH0.flsc3asxZpoWproDenaby1epHDBM2TCCWKSciQCihl0"; 
// both url and anon key can be in frontend, serivce key cannot


const supabase = createClient(
    supabaseUrl,
    supabaseAnonKey
);

const loginForm = document.getElementById("adminLoginForm");
const loginError = document.getElementById("loginError");
const logoutform = document.getElementById("logoutButton")

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    loginError.textContent = "";

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
    });

    if (error) {
        loginError.textContent = "Invalid email or password.";
        return;
    }

    if (!data.session) {
        loginError.textContent = "Unable to create login session.";
        return;
    }

    window.location.href = "./admin-dashboard.html";
});

logoutform.addEventListener("click", async () => {
        await supabase.auth.signOut();
        window.location.href = "./admin_login.html";
    });