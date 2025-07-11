from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import DailyReport, DailyReportDetail, UserProfile
import csv
from datetime import datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db import transaction

# Create your views here.

@staff_member_required
def export_csv(request):
    # レスポンスの設定
    response = HttpResponse(content_type='text/csv; charset=cp932')
    response['Content-Disposition'] = f'attachment; filename="daily_report_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    # CSVライターの設定
    writer = csv.writer(response)
    
    # ヘッダーの書き込み
    writer.writerow([
        '日付', 'ユーザー', '開始時間', '終了時間', '作業内容', '得意先', '担当者', 
        '報告事項', 'コメント', '上司確認', '提出状態'
    ])
    
    # 日報データの取得
    reports = DailyReport.objects.all().order_by('-date')
    
    # データの書き込み
    for report in reports:
        details = report.details.all()
        if details:
            for detail in details:
                writer.writerow([
                    report.date,
                    report.user.username if report.user else '',
                    detail.start_time,
                    detail.end_time,
                    detail.work_title or '',
                    detail.client or '',
                    detail.responsible_person or '',
                    report.remarks or '',
                    report.comment or '',
                    '確認済' if report.boss_confirmation else '未確認',
                    '提出済' if report.is_submitted else '下書き'
                ])
        else:
            # 詳細がない場合は空の行を追加
            writer.writerow([
                report.date,
                report.user.username if report.user else '',
                '', '', '', '', '',
                report.remarks or '',
                report.comment or '',
                '確認済' if report.boss_confirmation else '未確認',
                '提出済' if report.is_submitted else '下書き'
            ])
    
    return response

@staff_member_required
def import_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        try:
            # CSVファイルを読み込み
            decoded_file = csv_file.read().decode('cp932')
            csv_data = csv.reader(decoded_file.splitlines())
            
            # ヘッダー行をスキップ
            next(csv_data)
            
            imported_count = 0
            
            with transaction.atomic():
                for row in csv_data:
                    if len(row) >= 11:  # 必要な列数をチェック（11列に変更）
                        date_str = row[0]
                        username = row[1]
                        start_time = row[2] if row[2] else None
                        end_time = row[3] if row[3] else None
                        work_title = row[4] or ''
                        client = row[5] or ''
                        responsible_person = row[6] or ''
                        remarks = row[7] or ''
                        comment = row[8] or ''
                        boss_confirmation = row[9] == '確認済'
                        is_submitted = row[10] == '提出済'
                        
                        # ユーザーを取得
                        try:
                            user = User.objects.get(username=username) if username else None
                        except User.DoesNotExist:
                            continue
                        
                        # 日報を取得または作成
                        report, created = DailyReport.objects.get_or_create(
                            user=user,
                            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                            defaults={
                                'remarks': remarks,
                                'comment': comment,
                                'boss_confirmation': boss_confirmation,
                                'is_submitted': is_submitted,
                            }
                        )
                        
                        # 作業詳細を作成（時間が入力されている場合のみ）
                        if start_time and end_time:
                            DailyReportDetail.objects.create(
                                report=report,
                                start_time=datetime.strptime(start_time, '%H:%M:%S').time(),
                                end_time=datetime.strptime(end_time, '%H:%M:%S').time(),
                                work_title=work_title,
                                client=client,
                                responsible_person=responsible_person,
                            )
                        
                        imported_count += 1
            
            messages.success(request, f'{imported_count}件のデータをインポートしました。')
            
        except Exception as e:
            messages.error(request, f'インポートエラー: {str(e)}')
    
    return render(request, 'report/import.html')

def export_view(request):
    return render(request, 'report/export.html')

@staff_member_required
def export_users_csv(request):
    """ユーザー情報をCSVでエクスポート"""
    response = HttpResponse(content_type='text/csv; charset=cp932')
    response['Content-Disposition'] = f'attachment; filename="users_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # ヘッダーの書き込み
    writer.writerow([
        'ユーザー名', '姓', '名', 'メールアドレス', 'アクティブ', 'スタッフ権限', 
        'スーパーユーザー', 'グループ', '追加メールアドレス', '最終ログイン', '登録日'
    ])
    
    # ユーザーデータの取得
    users = User.objects.all().order_by('username')
    
    for user in users:
        # グループ名を取得
        groups = ', '.join([group.name for group in user.groups.all()])
        
        # UserProfileから追加メールアドレスを取得
        try:
            user_profile = UserProfile.objects.get(user=user)
            additional_emails = user_profile.additional_email or ''
        except UserProfile.DoesNotExist:
            additional_emails = ''
        
        writer.writerow([
            user.username,
            user.last_name,
            user.first_name,
            user.email,
            'アクティブ' if user.is_active else '無効',
            'あり' if user.is_staff else 'なし',
            'あり' if user.is_superuser else 'なし',
            groups,
            additional_emails,
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response
