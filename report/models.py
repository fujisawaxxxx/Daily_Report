from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class DailyReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ユーザー', null=True)
    date = models.DateField(verbose_name='日付')
    boss_confirmation = models.BooleanField(verbose_name='上司確認', default=False)
    remarks = models.TextField('報告事項', blank=True, null=True)
    comment = models.TextField('コメント', blank=True, null=True)
    is_submitted = models.BooleanField('提出', default=False)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    def __str__(self):
        return f"{self.date} - {self.user.username if self.user else '未設定'}"
    
    class Meta:
        verbose_name = '日報'
        verbose_name_plural = '日報'
        ordering = ['-date']

class DailyReportDetail(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='details', verbose_name='日報')
    start_time = models.TimeField(verbose_name='開始時間')
    end_time = models.TimeField(verbose_name='終了時間')
    work_title = models.CharField('作業内容', max_length=200, blank=True, null=True)
    client = models.CharField('得意先', max_length=70, blank=True, null=True)
    responsible_person = models.CharField('担当者', max_length=100, blank=True, null=True)
    
    def __str__(self):
        return ''  # 空文字列を返すように変更
    
    class Meta:
        verbose_name = '作業詳細'
        verbose_name_plural = '作業詳細'
        ordering = ['start_time']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='ユーザー')
    additional_email = models.EmailField('追加メールアドレス', blank=True, null=True, help_text='日報通知用の追加メールアドレス')
    
    def __str__(self):
        return f"{self.user.username}のプロファイル"
    
    class Meta:
        verbose_name = 'ユーザープロファイル'
        verbose_name_plural = 'ユーザープロファイル'
