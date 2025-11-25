$(document).ready(function() {
        $(".get-started").click(function(){
                $("#get-started").addClass("hide");
                if($("#login-block").hasClass("hide")){
                        $("#login-block").removeClass("hide");
                }

        });

        $("#submit_quiz_btn").click(function(e){
                e.preventDefault();
                validateBaseQuestionsForm();
                //loader();
     
        });
       /* $.ajax({
    url: "/api/data",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({ name: "Alice" }),
    success: function(res) {
        console.log(res);
    }
});*/
});

function loader(){
        $.get("/loading", function(response) {
        $("#loader").html(response);
                
                $("#loader").addClass("active");
                $('html, body').animate({
                        scrollTop: $("#loader").offset().top
                }, 30);
                $("body").addClass("locked");
        });
}

function validateBaseQuestionsForm(){
        var empty = "false";

    $("#quiz").find("[required]").each(function() {
        var obj  = $(this).val();
        if (obj == "") {
            empty = "true";
            //$("#quiz_errors").addClass("error"); // optional: highlight
            //$("#quiz_errors").html("Please fill in all required fields."); 
        } else {
                empty = "false";
            /*if($("#quiz_errors").hasClass("error")){
                $("#quiz_errors").removeClass("error");    
            }
            $("#quiz_errors").html("");
            loader();
            $("#submit_quiz_btn").attr("id","advance_quiz_btn");*/
        }
    });

    if (empty == "true") {
        $("#quiz_errors").addClass("error");
        $("#quiz_errors").html("Please fill in all required fields."); 
         $('html, body').animate({
                        scrollTop: $("#quiz_errors").offset().top
                }, 30);
    }else{
        if($("#quiz_errors").hasClass("error")){
                $("#quiz_errors").removeClass("error");    
            }
            $("#quiz_errors").html("");
            loader();
            $("#submit_quiz_btn").attr("id","advance_quiz_btn");
            checkTechnicalLevel();
    }
}

function checkTechnicalLevel(){
        //var technicalLevel = $("#question-66").val();
        //var technicalFamilar = $("#question-22").val();
        var currentSituation = $("#question-11").val();
        if(currentSituation.indexOf("Working Professional (Non-Tech)") > -1){
          technicalQuestionsExplore();
        }else{
         fixedTechnicalQuestions();       
        }
}

function createJsonDataBaseQuestionsInput(){
        var now = new Date();
var dateTime = now.toLocaleString();
var user_id = $("#user_id").val();
var responses = {
        Q1_current_status:{
                question:"What best describes your current situation?",
                answer: $("#question-11").val()

        },
        Q2_tech_familiarity:{
                question:"How familiar are you with technology and digital tools?",
                answer: $("#question-22").val()

        },
        Q3_tech_experience:{
                question:"Have you ever taken a course, training, or worked on a project related to tech?",
                answer:$("#question-33").val()

        },
        Q4_interest_area:{
                question:"Which of these areas interests you the most?",
                answer:$("#question-44").val()

        },
        Q5_motivation:{
                question:"What motivates you most to pursue a tech career?",
                answer: $("#question-55").val()

        },
        Q6_skill_level:{
                question:"How would you describe your current technical skill level?",
                answer: $("#question-66").val()

        },
        Q7_project_experience:{
                question:"Have you ever completed a personal or professional tech project?",
                answer: $("#question-77").val()

        },
        Q8_learning_preference:{
                question:"How do you prefer to learn new skills?",
                answer: $("#question-88").val()

        },
        Q9_time_commitment:{
                question:"How much time can you dedicate to learning weekly?",
                answer: $("#question-99").val()

        },
        Q10_goal:{
                question:"What is your main goal right now?",
                answer: $("#question-1010").val()

        },
}
var data = {
    timestamp:dateTime,
    user_id:user_id,
    responses: responses
};

  var baseQuestionsJson = JSON.stringify(data);
  return baseQuestionsJson;
}

function technicalQuestionsExplore(){
  var data = createJsonDataBaseQuestionsInput();
  $(".technical_questions").html("");
  $(".technical_questions").html(data);
  /*$.ajax({
    url: "http://127.0.0.1:7070/",
    method: "POST",
    contentType: "application/json",
    data: data,
    success: function(res) {
        console.log(res);
    }
});*/
}

function fixedTechnicalQuestions(){
        var data = createJsonDataBaseQuestionsInput();
         $(".technical_questions").html("");
  $(".technical_questions").html(data);
}