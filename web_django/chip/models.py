from django.db import models
# Create your models here.

class BrokerData(models.Model):
    broker = models.CharField(max_length=20, help_text="券商")
    broker_branch = models.CharField(max_length=20, help_text="據點")
    code = models.CharField(max_length=4, help_text="公司代碼")
    date = models.DateField(help_text="日期")
    buy = models.IntegerField(help_text="買進(張)")
    sell = models.IntegerField(help_text="賣出(張)")
    total = models.IntegerField(help_text="買賣總額(張)")
    net = models.IntegerField(help_text="買賣超(張)")

    def __str__(self):
        return f"{self.broker} - {self.broker_branch} {self.code} ({self.date})"
