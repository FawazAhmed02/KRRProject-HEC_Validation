console.log("Hello World!");

// accept files from form and make api call to /upload and send files to server - 3 files to be submitted
// submit button

// Path: static/main.js
const form = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const submitButton = document.getElementById("submitButton");

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const trnsfile = document.getElementById("trnsfile");
  const hecfile = document.getElementById("hecfile");
  const criteriafile = document.getElementById("criteriafile");
  console.log(trnsfile, hecfile, "trnsfile, hecfile");
  const formData = new FormData();
  formData.append("trnsfile", trnsfile.files[0]);
  formData.append("hecfile", hecfile.files[0]);
  formData.append("criteriafile", criteriafile.files[0]);

  //   for (let i = 0; i < files.length; i++) {
  //     let file = files[i];
  //     formData.append("files[]", file);
  //   }
  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      let courseContainer = document.getElementById("courseContainer");
      let creditCounter = document.getElementById("creditCount");
      let reasonContainer = document.getElementById("reasonContainer");
      //   let reason = document.getElementById("reasons");

      creditCounter.innerHTML = `<h1>Total Credit Hours: ${data.creditCount}</h1>`;

      data.allPossibleWays.forEach(function (category) {
        var categoryDiv = document.createElement("div");
        categoryDiv.classList.add("course-container");

        var categoryNameDiv = document.createElement("div");
        categoryNameDiv.classList.add("course-category");
        categoryNameDiv.textContent = Object.keys(category)[0];

        categoryDiv.appendChild(categoryNameDiv);

        var courseList = category[Object.keys(category)[0]];

        courseList.forEach(function (courses) {
          var ul = document.createElement("ul");
          ul.classList.add("course-list");

          courses.forEach(function (course) {
            var li = document.createElement("li");
            li.classList.add("course-item");

            var courseNameSpan = document.createElement("span");
            courseNameSpan.classList.add("course-name");
            courseNameSpan.textContent = course.courseName;

            var creditHourSpan = document.createElement("span");
            creditHourSpan.classList.add("credit-hour");
            creditHourSpan.textContent =
              " - " + course.creditHour + " credit hours";

            li.appendChild(courseNameSpan);
            li.appendChild(creditHourSpan);

            ul.appendChild(li);
          });

          categoryDiv.appendChild(ul);
        });

        courseContainer.appendChild(categoryDiv);
      });

      data.reasons.forEach(function (reason) {
        var reasonDiv = document.createElement("div");
        reasonDiv.classList.add("reason-container");

        var categoryDiv = document.createElement("div");
        categoryDiv.classList.add("reason-category");
        categoryDiv.textContent = reason.split(" ")[1].replace(/_/g, " ");

        var descriptionDiv = document.createElement("div");
        descriptionDiv.classList.add("reason-description");
        descriptionDiv.textContent = reason;

        reasonDiv.appendChild(categoryDiv);
        reasonDiv.appendChild(descriptionDiv);

        reasonContainer.appendChild(reasonDiv);
      });

      console.log(data);
    });
});
