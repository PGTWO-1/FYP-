from django.shortcuts import render

#/user/register
def register(request):
    return render(request,'register.html')