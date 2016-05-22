// TODO: refactor globals
var currentlySelectedFile = null;

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

jQuery.postJSON = function(url, args, callback) {
    args._xsrf = getCookie("_xsrf");
    console.log(args)
    $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
        success: function(response) {
        callback(eval("(" + response + ")"));
    }});
};

function refreshSelectedFile() {
    $.get("/a/file/" + currentlySelectedFile, function (data) {
        editor.setValue(data);
    });
}

function selectFile(path) {
    currentlySelectedFile = path;
    refreshSelectedFile();
}

function switchBranch(branch) {
    jQuery.postJSON("/a/switch_branch", {branch:branch}, function(data) {
        branchUpdated(branch);
    });
}

function branchUpdated(branch) {
   $("#selectedBranch").text(branch); 
   refreshSelectedFile();  // TODO: File may not exist in this branch
}

function saveSelectedFile() {
   var branch = $("#selectedBranch").text();
   if (!branch.startsWith("testenv-")) {
      // TODO: Use a nicer UI
      branch = prompt("Protected branch. Name of feature (lower case with hyphens only): ");
   }

   // TODO: Assumes tiny files for now:
   jQuery.postJSON("/a/file/" + currentlySelectedFile, {content:editor.getValue(), branch:branch}, function (data) {
      console.log("Successfully updated the file");
   });
}

