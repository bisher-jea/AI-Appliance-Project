const express = require("express");
const multer = require("multer");
const cors = require("cors");

const app = express();

app.use(cors());

const storage = multer.diskStorage({
    destination: function(req, file, cb) {
        cb(null, "uploads/");
    },
    filename: function(req, file, cb) {
        cb(null, Date.now() + "-" + file.originalname);
    }
});

const upload = multer({ storage: storage });

app.post(
    "/upload",
    upload.fields([
        { name: "nameplatePhoto", maxCount: 1 }
    ]),
    (req, res) => {

        console.log(req.body);

        console.log(req.files);

        res.send("Form submitted successfully!");

    }
);

app.listen(3000, () => {
    console.log("Server running on port 3000");
});