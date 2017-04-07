$(document).ready(function () {
    var ruleSet1 = {
        minlength: 8,
        maxlength: 8
    };


    $("form").validate({
        rules: {
            subject1: {
                required: true,
                minlength: 8,
                maxlength: 8
            },
            subject2: ruleSet1,
            subject3: ruleSet1,
            subject4: ruleSet1,
            subject5: ruleSet1,
        }
    });
    $("form").on('submit', function (e) {
        e.preventDefault();
        $.ajax({
            type: "POST",
            url: '/whatsdue',
            data: $("form").serialize(), // serializes the form's elements.
            success: function (data) {
                console.log(data)
                visualise_data(data)
            }
        });
    });

    function visualise_data(data) {
        var course;
        var assessment;
        var dueDate;
        var weighting;
        var normalizedDueDate;
        for (var i = 0; i < data.length; i++) {
            course = data[i][0];
            assessment = data[i][1];
            dueDate = data[i][2];
            weighting = data[i][3];
            normalizedDueDate = normalize_date(dueDate);
            $( "#results" ).append(course + " - " + assessment + 
            "<br> <strong> Listed Date: </strong>" + dueDate +"<br> <strong>Normalized date: </strong>" + normalizedDueDate + "<br> <br>");
        }
    }
    function normalize_date(dueDate) {
        return moment(dueDate).format('YYYY/MM/DD hh:mm:ss')
    }
});