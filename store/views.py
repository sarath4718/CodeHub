from django.shortcuts import render,redirect,get_object_or_404
from django.views.generic import View,FormView,CreateView,TemplateView
from store.forms import SignUpForm,SignInForm,UserProfileForm,ProjectForm,ResetPasswordForm
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from store.models import UserProfile,Project,WishListItem,Order
from django.contrib import messages
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from decouple import config
# Create your views here.

def send_email():
    send_mail(
    "Codehub Project Download",
    "You have successfully downloaded the project.",
    "sr4sarath18@gmail.com",
    ["nihasansin25@gmail.com"],
    fail_silently=False,
)


class SignUpView(CreateView):

    template_name = "register.html"

    form_class = SignUpForm
    
    success_url = reverse_lazy("signin")

    # def get(self,request,*args,**kwargs):

    #     form_instance = self.form_class()

    #     return render(request,self.template_name,{"form":form_instance})
    
    # def post(self,request,*args,**kwargs):

    #     form_instance = self.form_class(request.POST)

    #     if form_instance.is_valid():

    #         form_instance.save()

    #         print("account created")

    #         return redirect("signup")
    #     else:

    #         print("failed to create account")

    #         return render(request,self.template_name,{"form":form_instance})
        
class SignInView(FormView):

    template_name = "login.html"

    form_class = SignInForm

    def post(self,request,*args,**kwargs):

        form_instance = self.form_class(request.POST)

        if form_instance.is_valid():

            uname = form_instance.cleaned_data.get("username")

            pwd = form_instance.cleaned_data.get("password")

            user_object = authenticate(username = uname, password = pwd)

            if user_object:

                login(request,user_object)

                return redirect("index")
            
        return render(request,self.template_name,{"form":form_instance})



class IndexView(View):

    template_name = "index.html"

    def get(self, request,*args,**kwargs):

        qs = Project.objects.all().exclude(developer=request.user)

        return render(request,self.template_name,{"data":qs})

class LogOutView(View):

    def get(self,request,*args,**kwargs):

        logout(request)

        return redirect("signin")
    
class UserProfileEditView(View):

    template_name = "profile_edit.html"

    form_class = UserProfileForm

    def get(self,request,*args,**kwargs):

        #profile_object = UserProfile.objects.get(owner = request.user)

        profile_object = request.user.profile

        form_instance = self.form_class(instance=profile_object)

        return render(request,self.template_name,{"form":form_instance})
    def post(self,request,*Args,**kwargs):

        profile_instance = request.user.profile

        form_instance = self.form_class(request.POST,instance=profile_instance,files=request.FILES)

        if form_instance.is_valid():

            form_instance.save()

            return redirect("index")
        
        return render(request,self.template_name,{"form":form_instance})

class ProjectCreateView(View):

    template_name = "project_add.html"

    form_class = ProjectForm

    def get(self,request,*args,**kwargs):

        form_instance = self.form_class()

        return render(request,self.template_name,{"form":form_instance})
    
    def post(self,request,*args,**kwargs):

        form_instance = self.form_class(request.POST,files=request.FILES)

        if form_instance.is_valid():

            form_instance.instance.developer = request.user

            form_instance.save()

            return redirect("index")
        
        return render(request,self.template_name,{"form":form_instance})

class MyProjectListView(View):

    template_name = "my_projects.html"

    def get(self,request,*args,**kwargs):

        qs = Project.objects.filter(developer = request.user)

        return render(request,self.template_name,{"data":qs})
    
class ProjectUpdateView(View):

    template_name = "project_update.html"

    form_class = ProjectForm

    def get(self,request,*args,**kwargs):

        id = kwargs.get("pk")

        project_object = Project.objects.get(id=id)

        form_instance = self.form_class(instance=project_object)

        return render(request,self.template_name,{"form":form_instance})
    
    def post(self,request,*args,**kwargs):

        id = kwargs.get("pk")

        project_object = Project.objects.get(id=id)

        form_instance = self.form_class(request.POST,instance=project_object,files=request.FILES)

        if form_instance.is_valid():

            form_instance.save()

            return redirect("my-works")
        return render(request,self.template_name,{"form":form_instance})
    
class ProjectDetailView(View):

    template_name = "project_detail.html"

    def get(self,request,*args,**kwargs):

        id = kwargs.get("pk")

        qs = Project.objects.get(id=id)

        return render(request,self.template_name,{"data":qs})

class AddToWishListView(View):

    def get(self,request,*args,**kwargs):


        id = kwargs.get("pk")

        project_object = get_object_or_404(Project,id=id)

        try:

            request.user.basket.basket_item.create(project_object=project_object)

            messages.success(request,"item added successfully")
        except:
            messages.error(request,"Item is already added")

        return redirect("index")

class MyWishListView(View):

    template_name = "my_wishlist.html"

    def get(self,request,*args,**kwargs):

        qs = request.user.basket.basket_item.filter(is_order_placed = False)

        total = qs.values("project_object").aggregate(total=Sum("project_object__price")).get("total")

        print("total",total)

            

        return render(request,self.template_name,{"data":qs,"total":total})
    
class WishListItemDelete(View):

    def get(self,request,*args,**kwargs):

        id = kwargs.get("pk")

        WishListItem.objects.get(id = id).delete()

        return redirect("my-wishlist")

import razorpay
class CheckOutView(View):


    template_name = "checkout.html"

    def get(self,request,*args,**kwargs):

        # 1st step 

        KEY_ID = config('KEY_ID')

        KEY_SECRET = config('KEY_SECRET')

        #authenticate

        client = razorpay.Client(auth=(KEY_ID,KEY_SECRET))

        wish_list_total=request.user.basket.basket_item.filter(is_order_placed=False).values("project_object").aggregate(total=Sum("project_object__price")).get("total")

        data = { "amount": wish_list_total*100, "currency": "INR", "receipt": "order_rcptid_11" }

        payment = client.order.create(data=data)

        order_id=payment.get("id")

        order_object=Order.objects.create(order_id=order_id,customer=request.user)

        wishlist_items=request.user.basket.basket_item.filter(is_order_placed=False)

        for wi in wishlist_items:

            order_object.wishlist_item_objects.add(wi)

            wi.is_order_placed=True

            wi.save()

        return render(request,self.template_name,{"key_id":KEY_ID,"amount":wish_list_total,"order_id":order_id})


@method_decorator(csrf_exempt,name='dispatch')
class PaymentVerificationView(View):

    def post(self,request,*args,**kwargs):

        print(request.POST)

        KEY_ID = config('KEY_ID')

        KEY_SECRET = config('KEY_SECRET')

        client = razorpay.Client(auth=(KEY_ID,KEY_SECRET))

        try:

            client.utility.verify_payment_signature(request.POST)
           
            order_id = request.POST.get("razorpay_order_id")

            Order.objects.filter(order_id=order_id).update(is_paid = True)

            send_email()

        except:

            print("failed")

        return redirect("orders")

class MyOrdersView(View):

    template_name = "myorders.html"

    def get(self,request,*args,**kwargs):

        qs = Order.objects.filter(customer = request.user)

        return render(request,self.template_name,{"data":qs})
    
class ResetPasswordView(View):

    template_name = "password_reset.html"

    form_class = ResetPasswordForm

    def get(self,request,*args,**kwargs):

        form_instance = self.form_class()

        return render(request,self.template_name,{"form":form_instance})
    
    def post(self,request,*args,**kwargs):

        form_instance = self.form_class(request.POST)

        if form_instance.is_valid(): 

            username = form_instance.cleaned_data.get("username")

            email = form_instance.cleaned_data.get("email")

            password1 = form_instance.cleaned_data.get("password1")

            password2 = form_instance.cleaned_data.get("password2")

            print(username,email,password1,password2)

            try:

                assert password1==password2,"password mismatch"

                user_object = User.objects.get(username=username,email=email)

                user_object.set_password(password2)

                user_object.save()

                return redirect("signin")
            
            except Exception as e:

                messages.error(request,f"{e}")

                return render(request,self.template_name,{"form":form_instance})


           
        
        return render(request,self.template_name,{"form":form_instance})

                  