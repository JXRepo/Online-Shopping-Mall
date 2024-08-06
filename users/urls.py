from django.urls import path
from apps.users.views import UsernameCountView,RegisterView,LoginView,LogoutView
from apps.users.views import CenterView,EmailView,EmailVerifyView
from apps.users.views import AddressCreateView,AddressView,UserHistoryView
urlpatterns = [
    # Determine whether the user name is repeated
    path('usernames/<username:username>/count/',UsernameCountView.as_view()),
    path('register/',RegisterView.as_view()),
    path('login/',LoginView.as_view()),
    path('logout/',LogoutView.as_view()),
    path('info/',CenterView.as_view()),
    path('emails/',EmailView.as_view()),
    path('emails/verification/',EmailVerifyView.as_view()),
    path('addresses/create/',AddressCreateView.as_view()),
    path('addresses/',AddressView.as_view()),


    path('browse_histories/',UserHistoryView.as_view()),

]