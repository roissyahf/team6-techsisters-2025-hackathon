
function loader(action){
    if(action == "show"){
            $("#loader").addClass("active");
            $('html, body').animate({
                    scrollTop: $("#loader").offset().top
            }, 30);
            $("body").addClass("locked");
    }else{
          if($("#loader").hasClass("active")){
            $("#loader").removeClass("active");
            if($("body").hasClass("locked"))
              $("body").removeClass("locked");

        }  
    }   
}

$(document).ready(function() {
        $(".get-started").click(function(){
                $("#get-started").addClass("hide");
                if($("#login-block").hasClass("hide")){
                        $("#login-block").removeClass("hide");
                }

        });

        $("#submit_quiz_btn").click(function(e){
                e.preventDefault();
                loader('show');
                validateBaseQuestionsForm();
        });
      /* Technical Quiz Response */
        /*$('#tech_quiz_btn').click(function(e){
            e.preventDefault();
            loader('show');
            //Window.alert("HELLO");
            createJsonDataJobRolesOutput();
        });*/
});

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
           
            $("#submit_quiz_btn").attr("id","advance_quiz_btn");
            checkTechnicalLevel();
            
    }
}

function checkTechnicalLevel(){
        //var technicalLevel = $("#question-66").val();
        //var technicalFamilar = $("#question-22").val();
        var currentSituation = $("#question-11").val();
        if(currentSituation.indexOf("Working Professional (Non-Tech)") > -1){
          technicalQuestionsExplore();  //Calling API in here for Technical investigation
        }else{
         fixedTechnicalQuestions();    // Database Questions    
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
    user_profile:{
        timestamp:dateTime,
        user_id:user_id,
        responses: responses
   }
};

  var baseQuestionsJson = JSON.stringify(data);
  return baseQuestionsJson;
}

function parseTechnicalQuestionsJson(res){
    var jsonObj = JSON.parse(res); 
    var questionsObj = jsonObj.questions;
    var questionsJson = questionsObj;
    var htmlElement = "";
    var counter = 100;
    var user_id = $("#user_id").val();
    $.each(questionsJson, function(index, item) {
        counter++;
        htmlElement += '<h2 class="link_text tech_category cat-'+counter+'" data-key="'+item.competency+'">'+item.competency_name+'</h2>';
        htmlElement += '<label for="66">'+item.question_text+'<span class="req">*</span>';
        htmlElement += '<select name="" id="question-'+counter+'" class="tech_ques" required=""><option value="">-- choose --</option>';
        var selectOptions = item.options;
        var selectHtml = "";
        $.each(selectOptions, function(index, item) {
           selectHtml += '<option value="'+index+'">'+selectOptions[index]+'</option>';
        });
        htmlElement += selectHtml;
        htmlElement += '</select></label>';
        counter = counter + 1;
    }); 
htmlElement += '<input type="hidden" name="user_id" id="user_id" value="'+user_id+'">';
 htmlElement += '<input type="button" name="submit" id="tech_quiz_btn" class="hero-button btn btn-primary" value="Submit" onclick="createJsonDataJobRolesOutput();">';
    return htmlElement;
}
function technicalQuestionsExplore(){
  var data = createJsonDataBaseQuestionsInput();
  $(".base_questions").hide();
  $(".technical_questions").html("");
  //$(".technical_questions").html(data);
  $.ajax({
    url: "/generate_dynamic_questions",
    method: "POST",
    contentType: "application/json",
    dataType: "json",   
    data: data,
    success: function(res) {
        var htmlElement = parseTechnicalQuestionsJson(JSON.stringify(res));
         loader('hide');
        $(".technical_questions").html(htmlElement);
    },
        error: function() {
            $(".technical_questions").html("Error Occur: Please reload the page.");
        }
});
}

function fixedTechnicalQuestions(){
  var data = createJsonDataBaseQuestionsInput();
  $(".base_questions").hide();
  $(".technical_questions").html("");
  //$(".technical_questions").html(data);
  $.ajax({
    url: "/generate_dynamic_questions",
    method: "POST",
    contentType: "application/json",
    dataType: "json",   
    data: data,
    success: function(res) {
        var htmlElement = parseTechnicalQuestionsJson(JSON.stringify(res));
         loader('hide');
        $(".technical_questions").html(htmlElement);
         /*$('#tech_quiz_btn').click(function(e){
            e.preventDefault();
            loader('show');
            createJsonDataJobRolesOutput();
        });*/
    },
        error: function() {
            $(".technical_questions").html("Error Occur: Please reload the page.");
        }
});
}

/* Responses Functionality */
function createJsonDataBaseQuestionsOutput(){
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
    //base_persona_data:{
    user_profile:{
    timestamp:dateTime,
    user_id:user_id,
    responses: responses
   //}
}
};

  //var baseQuestionsJson = JSON.stringify(data);
  return data;
}
function createJsonDataTechQuestionsOutput(){
    var now = new Date();
    var dateTime = now.toLocaleString();
    var user_id = $("#user_id").val();
    var responses = [
         {
        competency: "C",
        competency_name: "Creative & User-Centricity",
        question_text: "When working on a visual design project, how do you ensure that the final product resonates with users?",
        selected_answer:{
            option_key: $("#question-101").val(),
            answer_text: $("#question-101 option:selected").text()
        }
    },
    {
        competency: "A",
        competency_name: "Logical & Structured Thinking",
        question_text: "How do you approach organizing your tasks when working on a project?",
        selected_answer: {
          option_key: $("#question-103").val(),
          answer_text: $("#question-103 option:selected").text()
        }
    },
         
         {
        competency: "B",
            competency_name: "Data & Analytical Insight",
            question_text: "When analyzing feedback for a project, how do you typically process the information?",
            selected_answer: {
              option_key: $("#question-105").val(),
              answer_text:  $("#question-105 option:selected").text()
            }

    },
         {
            competency: "D",
            competency_name: "Systemic & Risk Management",
            question_text: "How do you identify potential risks in your projects?",
            selected_answer: {
              option_key: $("#question-107").val(),
              answer_text:  $("#question-107 option:selected").text()
            }

    },
         {
          competency: "E",
          competency_name: "Communication & Stakeholder",
          question_text: "How do you keep stakeholders informed during a project?",
            selected_answer: {
             option_key: $("#question-109").val(),
              answer_text:  $("#question-109 option:selected").text()
        }
    },
         {
           competency: "F",
            competency_name: "Content & Language Fluency",
            question_text: "How do you approach writing content for your projects?",
            selected_answer: {
             option_key: $("#question-111").val(),
              answer_text:  $("#question-111 option:selected").text()
        }
    }

    ];
    var data = {
        //dynamic_questions_data:{
            user_profile:{
            timestamp:dateTime,
            user_id:user_id,
            responses: responses
       //}
     }
    }
    //var techQuestionsJson = JSON.stringify(data);
    return data;

}

function parseJobRolesJson(res){
    var jsonObj = JSON.parse(res); 
    var htmlElement = "";
    var counter = 900;
    var user_id = $("#user_id").val();
    var top_recommendations = jsonObj.top_recommendations;
    $("#page_heading").html("Select The Best Recommended Top Roles");
    $("#page_desc").html("Please select any role to proceed forward.");
    $.each(top_recommendations, function(index, item) {
        counter++;
       
            htmlElement += '<p><label for="item-'+counter+'" class="role_title"><input id="item-'+counter+'" type="radio" class="top_recommendations" name="top_recommendations" data.roleid="'+item.role_id+'" data.score="'+item.score+'" data.tfidf="'+item.tfidf+'" value="'+item.role_name+'">';
            htmlElement += item.role_name;
            htmlElement += '<br/><small class="role_desc">'+item.explanation+'</small></label></p>';
            
        counter = counter + 1;
    }); 
htmlElement += '<input type="hidden" name="user_id" id="user_id" value="'+user_id+'">';
 htmlElement += '<input type="button" name="submit" id="accept_role_btn" class="hero-button btn btn-primary" value="Accept Role" onclick="AcceptRole();">';
    return htmlElement;
}
function createJsonDataJobRolesOutput(){
    loader('show');
  var baseDataJson =  createJsonDataBaseQuestionsOutput();
  var techDataJson = createJsonDataTechQuestionsOutput();
  var jsonData =  JSON.stringify({ "base_persona_data": baseDataJson,"dynamic_questions_data": techDataJson });
  $(".base_questions").hide();
  $(".technical_questions").hide();
  $(".technical_roles").html("");
  
  //$(".technical_questions").html(data);
  $.ajax({
    url: "http://127.0.0.1:8080/recommend",
    type: "POST",
    contentType: "application/json",
    dataType: "json",
    data: jsonData,
    success: function(res) {
        loader('hide');
        var htmlElement = parseJobRolesJson(JSON.stringify(res));
        $(".technical_roles").html(htmlElement);
    },
    error: function() {
        $(".technical_questions").html("Error Occur: Please reload the page.");
    }
});
}

function AcceptRole(){
    var user_id = $("#user_id").val();
    var selectedRole = $('input[name="top_recommendations"]:checked').val();

     $(".base_questions").hide();
     $(".technical_questions").hide();
     $(".technical_roles").hide();

    var data = {
            user_id:user_id,
            selected_role: selectedRole
     };
    var outputJson = JSON.stringify(data);
    $.ajax({
        url: "/accept_tech_role",
        method: "POST",
        contentType: "application/json",
        dataType: "json",   
        data: outputJson,
        success: function(res) {
            console.log("Job Accepted");
        },
        error: function() {
            $(".technical_questions").html("Error Occur: Please reload the page.");
        }
});

}