/**
 * @file get-gov.js includes custom code for the .gov registrar.
 *
 * Constants and helper functions are at the top.
 * Event handlers are in the middle.
 * Initialization (run-on-load) stuff goes at the bottom.
 */


var DEFAULT_ERROR = "Please check this field for errors.";

var INFORMATIVE = "info";
var WARNING = "warning";
var ERROR = "error";
var SUCCESS = "success";

// <<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>>
// Helper functions.

/** Makes an element invisible. */
function makeHidden(el) {
  el.style.position = "absolute";
  el.style.left = "-100vw";
  // The choice of `visiblity: hidden`
  // over `display: none` is due to
  // UX: the former will allow CSS
  // transitions when the elements appear.
  el.style.visibility = "hidden";
}

/** Makes visible a perviously hidden element. */
function makeVisible(el) {
  el.style.position = "relative";
  el.style.left = "unset";
  el.style.visibility = "visible";
}

/** Creates and returns a live region element. */
function createLiveRegion(id) {
  const liveRegion = document.createElement("div");
  liveRegion.setAttribute("role", "region");
  liveRegion.setAttribute("aria-live", "polite");
  liveRegion.setAttribute("id", id + "-live-region");
  liveRegion.classList.add("usa-sr-only");
  document.body.appendChild(liveRegion);
  return liveRegion;
}

/** Announces changes to assistive technology users. */
function announce(id, text) {
  let liveRegion = document.getElementById(id + "-live-region");
  if (!liveRegion) liveRegion = createLiveRegion(id);
  liveRegion.innerHTML = text;
}

/**
 * Slow down event handlers by limiting how frequently they fire.
 *
 * A wait period must occur with no activity (activity means "this
 * debounce function being called") before the handler is invoked.
 *
 * @param {Function} handler - any JS function
 * @param {number} cooldown - the wait period, in milliseconds
 */
function debounce(handler, cooldown=600) {
  let timeout;
  return function(...args) {
    const context = this;
    clearTimeout(timeout);
    timeout = setTimeout(() => handler.apply(context, args), cooldown);
  }
}

/** Asyncronously fetches JSON. No error handling. */
function fetchJSON(endpoint, callback, url="/api/v1/") {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', url + endpoint);
    xhr.send();
    xhr.onload = function() {
      if (xhr.status != 200) return;
      callback(JSON.parse(xhr.response));
    };
    // nothing, don't care
    // xhr.onerror = function() { };
}

/** Modifies CSS and HTML when an input is valid/invalid. */
function toggleInputValidity(el, valid, msg=DEFAULT_ERROR) {
  if (valid) {
    el.setCustomValidity("");
    el.removeAttribute("aria-invalid");
    el.classList.remove('usa-input--error');
  } else {
    el.classList.remove('usa-input--success');
    el.setAttribute("aria-invalid", "true");
    el.setCustomValidity(msg);
    el.classList.add('usa-input--error');
  }
}

/** Display (or hide) a message beneath an element. */
function inlineToast(el, id, style, msg) {
  if (!el.id && !id) {
    console.error("Elements must have an `id` to show an inline toast.");
    return;
  }
  let toast = document.getElementById((el.id || id) + "--toast");
  if (style) {
    if (!toast) {
      // create and insert the message div
      toast = document.createElement("div");
      const toastBody = document.createElement("div");
      const p = document.createElement("p");
      toast.setAttribute("id", (el.id || id) + "--toast");
      toast.className = `usa-alert usa-alert--${style} usa-alert--slim`;
      toastBody.classList.add("usa-alert__body");
      p.classList.add("usa-alert__text");
      p.innerText = msg;
      toastBody.appendChild(p);
      toast.appendChild(toastBody);
      el.parentNode.insertBefore(toast, el.nextSibling);
    } else {
      // update and show the existing message div
      toast.className = `usa-alert usa-alert--${style} usa-alert--slim`;
      toast.querySelector("div p").innerText = msg;
      makeVisible(toast);
    }
  } else {
    if (toast) makeHidden(toast);
  }
}

function _checkDomainAvailability(el) {
  const callback = (response) => {
    toggleInputValidity(el, (response && response.available), msg=response.message);
    announce(el.id, response.message);
    if (el.validity.valid) {
      el.classList.add('usa-input--success');
      // use of `parentElement` due to .gov inputs being wrapped in www/.gov decoration
      inlineToast(el.parentElement, el.id, SUCCESS, response.message);
    } else {
      inlineToast(el.parentElement, el.id, ERROR, response.message);
    }
  }
  fetchJSON(`available/${el.value}`, callback);
}

/** Call the API to see if the domain is good. */
const checkDomainAvailability = debounce(_checkDomainAvailability);

/** Hides the toast message and clears the aira live region. */
function clearDomainAvailability(el) {
  el.classList.remove('usa-input--success');
  announce(el.id, "");
  // use of `parentElement` due to .gov inputs being wrapped in www/.gov decoration
  inlineToast(el.parentElement, el.id);
}

/** Runs all the validators associated with this element. */
function runValidators(el) {
  const attribute = el.getAttribute("validate") || "";
  if (!attribute.length) return;
  const validators = attribute.split(" ");
  let isInvalid = false;
  for (const validator of validators) {
    switch (validator) {
      case "domain":
        checkDomainAvailability(el);
        break;
    }
  }
  toggleInputValidity(el, !isInvalid);
}

/** Clears all the validators associated with this element. */
function clearValidators(el) {
  const attribute = el.getAttribute("validate") || "";
  if (!attribute.length) return;
  const validators = attribute.split(" ");
  for (const validator of validators) {
    switch (validator) {
      case "domain":
        clearDomainAvailability(el);
        break;
    }
  }
  toggleInputValidity(el, true);
}

// <<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>>
// Event handlers.

/** On input change, handles running any associated validators. */
function handleInputValidation(e) {
  clearValidators(e.target);
  if (e.target.hasAttribute("auto-validate")) runValidators(e.target);
}

/** On button click, handles running any associated validators. */
function handleValidationClick(e) {
  const attribute = e.target.getAttribute("validate-for") || "";
  if (!attribute.length) return;
  const input = document.getElementById(attribute);
  runValidators(input);
}

// <<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>><<>>
// Initialization code.

/**
 * An IIFE that will attach validators to inputs.
 *
 * It looks for elements with `validate="<type> <type>"` and adds change handlers.
 * 
 * These handlers know about two other attributes:
 *  - `validate-for="<id>"` creates a button which will run the validator(s) on <id>
 *  - `auto-validate` will run validator(s) when the user stops typing (otherwise,
 *     they will only run when a user clicks the button with `validate-for`)
 */
 (function validatorsInit() {
  "use strict";
  const needsValidation = document.querySelectorAll('[validate]');
  for(const input of needsValidation) {
    input.addEventListener('input', handleInputValidation);
  }
  const activatesValidation = document.querySelectorAll('[validate-for]');
  for(const button of activatesValidation) {
    button.addEventListener('click', handleValidationClick);
  }
})();


/**
 * An IIFE that attaches a click handler for our dynamic nameservers form
 *
 * Only does something on a single page, but it should be fast enough to run
 * it everywhere.
 */
(function prepareNameserverForms() {
  let serverForm = document.querySelectorAll(".server-form");
  let container = document.querySelector("#form-container");
  let addButton = document.querySelector("#add-nameserver-form");
  let totalForms = document.querySelector("#id_form-TOTAL_FORMS");

  let formNum = serverForm.length-1;
  if (addButton)
    addButton.addEventListener('click', addForm);

  function addForm(e){
      let newForm = serverForm[2].cloneNode(true);
      let formNumberRegex = RegExp(`form-(\\d){1}-`,'g');
      let formLabelRegex = RegExp(`Name server (\\d){1}`, 'g');
      let formExampleRegex = RegExp(`ns(\\d){1}`, 'g');

      formNum++;
      newForm.innerHTML = newForm.innerHTML.replace(formNumberRegex, `form-${formNum}-`);
      newForm.innerHTML = newForm.innerHTML.replace(formLabelRegex, `Name server ${formNum+1}`);
      newForm.innerHTML = newForm.innerHTML.replace(formExampleRegex, `ns${formNum+1}`);
      container.insertBefore(newForm, addButton);
      newForm.querySelector("input").value = "";

      totalForms.setAttribute('value', `${formNum+1}`);
  }
})();

function prepareDeleteButtons() {
  let deleteButtons = document.querySelectorAll(".delete-record");
  let totalForms = document.querySelector("#id_form-TOTAL_FORMS");

  // Loop through each delete button and attach the click event listener
  deleteButtons.forEach((deleteButton) => {
    deleteButton.addEventListener('click', removeForm);
  });

  function removeForm(e){
    let formToRemove = e.target.closest(".ds-record");
    formToRemove.remove();
    let forms = document.querySelectorAll(".ds-record");
    let formNum2 = forms.length;
    totalForms.setAttribute('value', `${formNum2}`);

    // We need to fix the indicies of every existing form otherwise 
    // the frontend and backend will not match and will error on submit
    // let formNumberRegex = RegExp(`form-(\\d){1}-`,'g');
    // let formLabelRegex = RegExp(`DS Data record (\\d){1}`, 'g');
    // forms.forEach((form, index) => {
    //   form.innerHTML = form.innerHTML.replace(formNumberRegex, `form-${index}-`);
    //   form.innerHTML = form.innerHTML.replace(formLabelRegex, `DS Data Record ${index+1}`);
    // });



    let formNumberRegex = RegExp(`form-(\\d){1}-`, 'g');
    let formLabelRegex = RegExp(`DS Data record (\\d){1}`, 'g');

    forms.forEach((form, index) => {
      // Iterate over child nodes of the current element
      Array.from(form.querySelectorAll('label, input, select')).forEach((node) => {
        // Iterate through the attributes of the current node
        Array.from(node.attributes).forEach((attr) => {
          // Check if the attribute value matches the regex
          if (formNumberRegex.test(attr.value)) {
            // Replace the attribute value with the updated value
            attr.value = attr.value.replace(formNumberRegex, `form-${index}-`);
          }
        });
      });

      Array.from(form.querySelectorAll('h2, legend')).forEach((node) => {
        node.textContent = node.textContent.replace(formLabelRegex, `DS Data record ${index + 1}`);
      });
    
    });




  }
}

/**
 * An IIFE that attaches a click handler for our dynamic DNSSEC forms
 *
 */
(function prepareDNSSECForms() {
  let serverForm = document.querySelectorAll(".ds-record");
  let container = document.querySelector("#form-container");
  let addButton = document.querySelector("#add-ds-form");
  let totalForms = document.querySelector("#id_form-TOTAL_FORMS");

  // Attach click event listener on the delete buttons of the existing forms
  prepareDeleteButtons();

  if (addButton) {
    addButton.addEventListener('click', addForm);
  }

  function addForm(e){
      let forms = document.querySelectorAll(".ds-record");
      let formNum = forms.length;
      let newForm = serverForm[0].cloneNode(true);
      let formNumberRegex = RegExp(`form-(\\d){1}-`,'g');
      let formLabelRegex = RegExp(`DS Data record (\\d){1}`, 'g');

      formNum++;
      newForm.innerHTML = newForm.innerHTML.replace(formNumberRegex, `form-${formNum-1}-`);
      newForm.innerHTML = newForm.innerHTML.replace(formLabelRegex, `DS Data record ${formNum}`);
      container.insertBefore(newForm, addButton);

      let inputs = newForm.querySelectorAll("input");
      // Reset the values of each input to blank
      inputs.forEach((input) => {
        input.classList.remove("usa-input--error");
        if (input.type === "text" || input.type === "number" || input.type === "password") {
          input.value = ""; // Set the value to an empty string
          
        } else if (input.type === "checkbox" || input.type === "radio") {
          input.checked = false; // Uncheck checkboxes and radios
        }
      });

      // Reset any existing validation classes
      let selects = newForm.querySelectorAll("select");
      selects.forEach((select) => {
        select.classList.remove("usa-input--error");
        select.selectedIndex = 0; // Set the value to an empty string
      });

      let labels = newForm.querySelectorAll("label");
      labels.forEach((label) => {
        label.classList.remove("usa-label--error");
      });

      let usaFormGroups = newForm.querySelectorAll(".usa-form-group");
      usaFormGroups.forEach((usaFormGroup) => {
        usaFormGroup.classList.remove("usa-form-group--error");
      });

      // Remove any existing error messages
      let usaErrorMessages = newForm.querySelectorAll(".usa-error-message");
      usaErrorMessages.forEach((usaErrorMessage) => {
        let parentDiv = usaErrorMessage.closest('div');
        if (parentDiv) {
          parentDiv.remove(); // Remove the parent div if it exists
        }
      });

      totalForms.setAttribute('value', `${formNum}`);

      // Attach click event listener on the delete buttons of the new form
      prepareDeleteButtons();

      // We need to fix the indicies of every existing form otherwise 
      // the frontend and backend will not match and will error on submit
      // forms.forEach((form, index) => {
      //   form.innerHTML = form.innerHTML.replace(formNumberRegex, `form-${index}-`);
      //   form.innerHTML = form.innerHTML.replace(formLabelRegex, `DS Data Record ${index+1}`);
      // });
  }

})();


// (function prepareCancelButtons() {
//   const cancelButton = document.querySelector('.btn-cancel');

//   if (cancelButton) {
//       cancelButton.addEventListener('click', () => {

//           // Option 2: Redirect to another page (e.g., the homepage)

//           localStorage.clear(); // Clear all localStorage data
//           sessionStorage.clear(); // Clear all sessionStorage data

//           location.reload();
//       });
//   }
// })();


// /**
//  * An IIFE that attaches a click handler on form cancel buttons
//  *
//  */
// (function prepareCancelButtons() {
//   const cancelButton = document.querySelector('.btn-cancel');

//   const formsetContainer = document.querySelector('#form-container');
//   const originalFormHTML = document.querySelector('.ds-record').innerHTML;
//   const numberOfFormsToReset = document.querySelectorAll('.ds-record').length;
//   const addNewRecordButton = document.querySelector('#add-ds-form');
//   const submitButton = document.querySelector('button[type="submit"]');

//   if (cancelButton) {
//     cancelButton.addEventListener('click', () => {
//       // Reset the form to its initial values
//       const form = document.querySelector('form');
//       resetForm(form);
//     });
//   }

//   function resetForm(form) {

//     // Remove all existing forms within the container
//     formsetContainer.innerHTML = '';
//     for (let i = 0; i < numberOfFormsToReset; i++) {
//       formsetContainer.innerHTML += originalFormHTML;
//     }
//     formsetContainer.innerHTML += addNewRecordButton
//     formsetContainer.innerHTML += submitButton

//     const dsRecords = form.querySelectorAll('.ds-record');

//     dsRecords.forEach((record) => {
//       const initialValuesField = record.querySelector('.initial-values');
//       const formFields = record.querySelectorAll('input, textarea, select');

//       if (initialValuesField) {
//         const initialValues = JSON.parse(initialValuesField.value);

//         formFields.forEach((field) => {
//           const fieldName = field.name;
//           if (fieldName in initialValues) {
//             field.value = initialValues[fieldName];
//           } else {
//             field.value = ''; // Set to empty if no initial value
//           }
//         });
//       }
//     });
//   }
// })();


/**
 * 
 *
 */
(function toggleDNSSECWarning() {
  document.getElementById("toggler1").addEventListener("click", function () {
    var element = document.getElementById("step-1");
    var element2 = document.getElementById("step-2");
    element.classList.toggle("display-none");
    element2.classList.toggle("display-none");
  });

  document.getElementById("toggler2").addEventListener("click", function () {
    var element = document.getElementById("step-1");
    var element2 = document.getElementById("step-2");
    element.classList.toggle("display-none");
    element2.classList.toggle("display-none");
  });
})();