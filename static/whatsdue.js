$(document).ready(function () {
    // The course and assessment urls to get profile and assessment info.
    var courseUrl = 'https://www.uq.edu.au/study/course.html?course_code=';
    var assessmentUrl = 'https://www.courses.uq.edu.au/student_section_report' +
        '.php?report=assessment&profileIds=';

    /**
     * Gets the profile id for a course given its course code.
     *
     * @param {string} course code (eg. CSSE2310)
     * @return {!Promise} A promise that resolves with the profile id
     *                    or an error.
     */
    function getProfileId(course) {
        return new Promise((resolve, reject) => {
            var urlforsubject = courseUrl + course
            $.ajax({
                url: urlforsubject,
                type: 'GET',
                dataType: 'html',
                jsonpCallback: 'callback',
                success: function (data) {
                    // Look for first instance of `/profileId=`. Will always point
                    // to the latest profile id for the course. If there is no
                    // profileId, check to ensure the course code is valid and return
                    // the relevant error message.
                    var profileID = String(data.match(/profileId=\d*/));
                    if (profileID !== 'null') {
                        resolve(profileID.replace('profileId=', ''));
                    } else if (body.match(/is not a valid course code/) ||
                        body.match(/Unable to find course code/)) {
                        reject(course + ' is not a valid course code.');
                    } else {
                        reject(course + ' has no available course profiles.');
                    }
                },
                error: function (data) {
                    reject('There was an error getting the course profile.');
                    return;
                }
            });
        });
    }

    /**
     * Parses the assessment data provided in the assessment url and returns
     * an array of assessments.
     *
     * @param {string} url linking to the assessment data
     * @return {!Promise} A promise that resolves with an array of assessments
     *                    or an error.
     */
    function parseAssessmentData(url) {
        return new Promise(resolve => {
            $.ajax({
                url: url,
                type: 'GET',
                success: function (data) {
                    var $ = cheerio.load(body);
                    var assessment = '_*WARNING:* Assessment information may ' +
                        'vary/change/be entirely different! Use ' +
                        'at your own discretion_\r\n>>>';

                    // Look for the tblborder class, which is the assessment data
                    // table, then loop over its children starting at index 1 to
                    // skip over the column headers (subject, task, due date and
                    // weighting).
                    // TODO(mitch): make this less ugly and bleh.
                    // Note: Formatting of assessment data is inconsistent and may
                    //       look ugly. Soz.
                    $('.tblborder').children().slice(1).each((index, element) => {
                        var columns = $(element).children();

                        var subject = $(columns[0]).find('div')
                            .text().trim().slice(0, 8);
                        var task = $(columns[1]).find('div')
                            .html().trim().replace('<br>', ' - ');
                        var dueDate = $(columns[2]).find('div')
                            .text().trim();
                        var weighting = $(columns[3]).find('div')
                            .text().trim();

                        if (!subject || !task || !dueDate || !weighting) {
                            reject('There was an error parsing the assessment.');
                            return;
                        }

                        assessment += '*' + subject + '*: ' +
                            '`' + task + '` ' +
                            '_(' + dueDate + ')_ ' +
                            '*' + weighting + '*\r\n';
                    });
                    resolve(assessment);
                },
                error: function (data) {
                    reject('There was an error getting the assessment.');
                    return;
                }
            });
        });
    }

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
    function print_data(data) {
        $("#response").text(data.toString());
    }

    $("form").on('submit', function (e) {
        e.preventDefault();
        var courseList = []
        if ($("#subject1").val()) {
            courseList.push($("#subject1").val())
        }
        if ($("#subject2").val()) {
            courseList.push($("#subject2").val())
        }
        if ($("#subject3").val()) {
            courseList.push($("#subject3").val())
        }
        if ($("#subject4").val()) {
            courseList.push($("#subject4").val())
        }
        if ($("#subject5").val()) {
            courseList.push($("#subject5").val())
        }

        // Create a Promise for each course.
        var profileResponses = [];
        for (var i = 0; i < courseList.length; i++) {
            profileResponses.push(getProfileId(courseList[i].toUpperCase()));
        }

        // Resolve all the Promises to obtain an array of profile ids. Join
        // them together to create the necessary assessment url to parse and
        // display back to the user. Print any errors that occured.
        Promise.all(profileResponses)
            .then(profiles => assessmentUrl + profiles.join())
            .then(url => parseAssessmentData(url))
            .then(assessment => print_data(assessment))
            .catch(error => print_data(error));
    });
});