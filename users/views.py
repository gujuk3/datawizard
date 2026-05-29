from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import EmailVerificationToken, PasswordResetToken
from .serializers import RegisterSerializer, UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token_obj = EmailVerificationToken.objects.create(user=user)
        verify_url = f"{settings.FRONTEND_URL}/verify-email/{token_obj.token}"
        try:
            send_mail(
                subject='DataWizard - Email Adresinizi Doğrulayın',
                message=(
                    f"Merhaba {user.username},\n\n"
                    f"DataWizard hesabınızı doğrulamak için aşağıdaki bağlantıya tıklayın:\n\n"
                    f"{verify_url}\n\n"
                    f"Bu bağlantıyı siz talep etmediyseniz bu emaili görmezden gelebilirsiniz."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({
                'error': f'Hesap oluşturuldu fakat doğrulama emaili gönderilemedi: {str(e)}',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({
            'message': 'Kayıt başarılı. Lütfen email adresinizi doğrulayın.',
            'email': user.email,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, token):
    token_obj = get_object_or_404(EmailVerificationToken, token=token, is_used=False)
    user = token_obj.user
    user.is_verified = True
    user.save()
    token_obj.is_used = True
    token_obj.save()
    refresh = RefreshToken.for_user(user)
    return Response({
        'message': 'Email doğrulandı! Giriş yapılıyor...',
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    })


class VerifiedTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_verified:
            raise AuthenticationFailed(
                detail='Email adresinizi doğrulamanız gerekiyor.',
                code='email_not_verified',
            )
        return data


class VerifiedTokenObtainPairView(TokenObtainPairView):
    serializer_class = VerifiedTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get('email', '').strip()
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
        token_obj = PasswordResetToken.objects.create(user=user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token_obj.token}"
        send_mail(
            subject='DataWizard - Şifre Sıfırlama',
            message=(
                f"Merhaba {user.username},\n\n"
                f"Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın (1 saat geçerli):\n\n"
                f"{reset_url}\n\n"
                f"Bu isteği siz yapmadıysanız bu emaili görmezden gelebilirsiniz."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except User.DoesNotExist:
        pass
    # Always return 200 — don't reveal if email exists
    return Response({'message': 'Eğer bu email kayıtlıysa sıfırlama bağlantısı gönderildi.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    token = request.data.get('token', '')
    new_password = request.data.get('new_password', '')

    if not token or not new_password:
        return Response({'error': 'Token ve yeni şifre gereklidir.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(new_password) < 8:
        return Response({'error': 'Şifre en az 8 karakter olmalıdır.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token_obj = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        return Response({'error': 'Geçersiz bağlantı.'}, status=status.HTTP_400_BAD_REQUEST)

    if not token_obj.is_valid():
        return Response({'error': 'Bu bağlantının süresi dolmuş veya daha önce kullanılmış.'}, status=status.HTTP_400_BAD_REQUEST)

    user = token_obj.user
    user.set_password(new_password)
    user.save()
    token_obj.is_used = True
    token_obj.save()

    return Response({'message': 'Şifreniz başarıyla güncellendi. Giriş yapabilirsiniz.'})
