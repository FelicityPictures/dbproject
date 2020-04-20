function groupDisplay(checkbox){
    //If it is checked.
    if(checkbox.checked){
        document.getElementById("postForm--groups").classList.add("displayNone");
    }
    //If it has been unchecked.
    else{
        document.getElementById("postForm--groups").classList.remove("displayNone");
    }
}
