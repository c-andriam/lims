(function () {
    "use strict";
    var form = document.getElementById("trimeta-repetitions-form");
    if (!form) { return; }
    var rows = document.getElementById("trimeta-repetition-rows");
    var remove = document.getElementById("trimeta-remove-repetition");
    function update() { remove.disabled = rows.children.length <= 2; }
    document.getElementById("trimeta-add-repetition").addEventListener("click", function () {
        var number = rows.children.length + 1;
        var row = document.createElement("div");
        row.className = "form-group";
        var label = document.createElement("label");
        label.htmlFor = "repetition-" + number;
        label.textContent = "Répétition " + number;
        var input = document.createElement("input");
        input.type = "text";
        input.inputMode = "decimal";
        input.name = "repetitions:list";
        input.id = label.htmlFor;
        input.className = "form-control";
        input.required = true;
        row.appendChild(label);
        row.appendChild(input);
        rows.appendChild(row);
        update();
        input.focus();
    });
    remove.addEventListener("click", function () {
        if (rows.children.length <= 2) { return; }
        var row = rows.lastElementChild;
        if (row.querySelector("input").value && !window.confirm("Retirer cette répétition et sa valeur ?")) { return; }
        row.remove();
        update();
    });
    update();
    form.addEventListener("submit", function () {
        form.querySelector("button[type=submit]").disabled = true;
    });
}());
