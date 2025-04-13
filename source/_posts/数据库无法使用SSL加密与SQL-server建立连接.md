---
title: 数据库无法使用SSL加密与SQL_server建立连接
date: 2023-05-02 23:01:04
tags: ["chatGPT", "SQL server","SSL"]
cover: http://sunowc60i.hd-bkt.clouddn.com/cover12.png
---

Model: Default (GPT-3.5)

> com.microsoft.sqlserver.jdbc.SQLServerException: 驱动程序无法通过使用安全套接字层(SSL)加密与 SQL Server 建立安全连接。错误:“PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target”。 ClientConnectionId:f885fd47-0376-4231-a88f-bc248715569c at com.microsoft.sqlserver.jdbc.SQLServerConnection.terminate(SQLServerConnection.java:3937) at com.microsoft.sqlserver.jdbc.TDSChannel.enableSSL(IOBuffer.java:1950) at com.microsoft.sqlserver.jdbc.SQLServerConnection.connectHelper(SQLServerConnection.java:3456) at com.microsoft.sqlserver.jdbc.SQLServerConnection.login(SQLServerConnection.java:3077) at com.microsoft.sqlserver.jdbc.SQLServerConnection.connectInternal(SQLServerConnection.java:2919) at com.microsoft.sqlserver.jdbc.SQLServerConnection.connect(SQLServerConnection.java:1787) at com.microsoft.sqlserver.jdbc.SQLServerDriver.connect(SQLServerDriver.java:1229) at java.sql.DriverManager.getConnection(DriverManager.java:664) at java.sql.DriverManager.getConnection(DriverManager.java:247) at com.chen.dao.BaseDao.getConnection(BaseDao.java:35) at com.chen.dao.Info.InfoDaoImpl.getAll(InfoDaoImpl.java:22) at com.chen.service.Info.InfoServiceImpl.getAll(InfoServiceImpl.java:12) at com.chen.servlet.Info.InfoServlet.doGet(InfoServlet.java:30) at javax.servlet.http.HttpServlet.service(HttpServlet.java:529) at javax.servlet.http.HttpServlet.service(HttpServlet.java:623) at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:209) at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:153) at org.apache.tomcat.websocket.server.WsFilter.doFilter(WsFilter.java:51) at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:178) at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:153) at com.chen.filter.CharacterEncodingFilter.doFilter(CharacterEncodingFilter.java:18) at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:178) at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:153) at org.apache.catalina.core.StandardWrapperValve.invoke(StandardWrapperValve.java:167) at org.apache.catalina.core.StandardContextValve.invoke(StandardContextValve.java:90) at org.apache.catalina.authenticator.AuthenticatorBase.invoke(AuthenticatorBase.java:481) at org.apache.catalina.core.StandardHostValve.invoke(StandardHostValve.java:130) at org.apache.catalina.valves.ErrorReportValve.invoke(ErrorReportValve.java:93) at org.apache.catalina.valves.AbstractAccessLogValve.invoke(AbstractAccessLogValve.java:673) at org.apache.catalina.core.StandardEngineValve.invoke(StandardEngineValve.java:74) at org.apache.catalina.connector.CoyoteAdapter.service(CoyoteAdapter.java:343) at org.apache.coyote.http11.Http11Processor.service(Http11Processor.java:389) at org.apache.coyote.AbstractProcessorLight.process(AbstractProcessorLight.java:63) at org.apache.coyote.AbstractProtocol$ConnectionHandler.process(AbstractProtocol.java:926) at org.apache.tomcat.util.net.NioEndpoint$SocketProcessor.doRun(NioEndpoint.java:1791) at org.apache.tomcat.util.net.SocketProcessorBase.run(SocketProcessorBase.java:52) at org.apache.tomcat.util.threads.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1191) at org.apache.tomcat.util.threads.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:659) at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61) at java.lang.Thread.run(Thread.java:750) Caused by: javax.net.ssl.SSLHandshakeException: PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target at sun.security.ssl.Alert.createSSLException(Alert.java:131) at sun.security.ssl.TransportContext.fatal(TransportContext.java:324) at sun.security.ssl.TransportContext.fatal(TransportContext.java:267) at sun.security.ssl.TransportContext.fatal(TransportContext.java:262) at sun.security.ssl.CertificateMessage$T12CertificateConsumer.checkServerCerts(CertificateMessage.java:654) at sun.security.ssl.CertificateMessage$T12CertificateConsumer.onCertificate(CertificateMessage.java:473) at sun.security.ssl.CertificateMessage$T12CertificateConsumer.consume(CertificateMessage.java:369) at sun.security.ssl.SSLHandshake.consume(SSLHandshake.java:377) at sun.security.ssl.HandshakeContext.dispatch(HandshakeContext.java:444) at sun.security.ssl.HandshakeContext.dispatch(HandshakeContext.java:422) at sun.security.ssl.TransportContext.dispatch(TransportContext.java:182) at sun.security.ssl.SSLTransport.decode(SSLTransport.java:152) at sun.security.ssl.SSLSocketImpl.decode(SSLSocketImpl.java:1397) at sun.security.ssl.SSLSocketImpl.readHandshakeRecord(SSLSocketImpl.java:1305) at sun.security.ssl.SSLSocketImpl.startHandshake(SSLSocketImpl.java:440) at com.microsoft.sqlserver.jdbc.TDSChannel.enableSSL(IOBuffer.java:1839) ... 38 more Caused by: sun.security.validator.ValidatorException: PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target at sun.security.validator.PKIXValidator.doBuild(PKIXValidator.java:456) at sun.security.validator.PKIXValidator.engineValidate(PKIXValidator.java:323) at sun.security.validator.Validator.validate(Validator.java:271) at sun.security.ssl.X509TrustManagerImpl.validate(X509TrustManagerImpl.java:315) at sun.security.ssl.X509TrustManagerImpl.checkTrusted(X509TrustManagerImpl.java:234) at sun.security.ssl.X509TrustManagerImpl.checkServerTrusted(X509TrustManagerImpl.java:110) at com.microsoft.sqlserver.jdbc.HostNameOverrideX509TrustManager.checkServerTrusted(SQLServerTrustManager.java:86) at sun.security.ssl.AbstractTrustManagerWrapper.checkServerTrusted(SSLContextImpl.java:1258) at sun.security.ssl.CertificateMessage$T12CertificateConsumer.checkServerCerts(CertificateMessage.java:638) ... 49 more Caused by: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target at sun.security.provider.certpath.SunCertPathBuilder.build(SunCertPathBuilder.java:141) at sun.security.provider.certpath.SunCertPathBuilder.engineBuild(SunCertPathBuilder.java:126) at java.security.cert.CertPathBuilder.build(CertPathBuilder.java:280) at sun.security.validator.PKIXValidator.doBuild(PKIXValidator.java:451) ... 57 more com.microsoft.sqlserver.jdbc.SQLServerException: 驱动程序无法通过使用安全套接字层(SSL)加密与 SQL Server 建立安全连接。错误:“PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target”。 ClientConnectionId:ee5bed32-43c1-4697-8af0-bd346a85d26a at com.microsoft.sqlserver.jdbc.SQLServerConnection.terminate(SQLServerConnection.java:3937) at com.microsoft.sqlserver.jdbc.TDSChannel.enableSSL(IOBuffer.java:1950) at com.microsoft.sqlserver.jdbc.SQLServerConnection.connectHelper(SQLServerConnection.java:3456) at com.microsoft.sqlserver.jdbc.SQLServerConnection.login(SQLServerConnection.java:3077) at com.microsoft.sqlserver.jdbc.SQLServerConnection.connectInternal(SQLServerConnection.java:2919) at com.microsoft.sqlserver.jdbc.SQLServerConnection.connect(SQLServerConnection.java:1787) at com.microsoft.sqlserver.jdbc.SQLServerDriver.connect(SQLServerDriver.java:1229) at java.sql.DriverManager.getConnection(DriverManager.java:664) at java.sql.DriverManager.getConnection(DriverManager.java:247) at com.chen.dao.BaseDao.getConnection(BaseDao.java:35) at com.chen.dao.Info.InfoDaoImpl.getAll(InfoDaoImpl.java:22) at com.chen.service.Info.InfoServiceImpl.getAll(InfoServiceImpl.java:12) at com.chen.servlet.Info.InfoServlet.doGet(InfoServlet.java:30) at javax.servlet.http.HttpServlet.service(HttpServlet.java:529) at javax.servlet.http.HttpServlet.service(HttpServlet.java:623) at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:209) at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:153) at org.apache.tomcat.websocket.server.WsFilter.doFilter(WsFilter.java:51) at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:178) at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:153) at com.chen.filter.CharacterEncodingFilter.doFilter(CharacterEncodingFilter.java:18) at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:178) at org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:153) at org.apache.catalina.core.StandardWrapperValve.invoke(StandardWrapperValve.java:167) at org.apache.catalina.core.StandardContextValve.invoke(StandardContextValve.java:90) at org.apache.catalina.authenticator.AuthenticatorBase.invoke(AuthenticatorBase.java:481) at org.apache.catalina.core.StandardHostValve.invoke(StandardHostValve.java:130) at org.apache.catalina.valves.ErrorReportValve.invoke(ErrorReportValve.java:93) at org.apache.catalina.valves.AbstractAccessLogValve.invoke(AbstractAccessLogValve.java:673) at org.apache.catalina.core.StandardEngineValve.invoke(StandardEngineValve.java:74) at org.apache.catalina.connector.CoyoteAdapter.service(CoyoteAdapter.java:343) at org.apache.coyote.http11.Http11Processor.service(Http11Processor.java:389) at org.apache.coyote.AbstractProcessorLight.process(AbstractProcessorLight.java:63) at org.apache.coyote.AbstractProtocol$ConnectionHandler.process(AbstractProtocol.java:926) at org.apache.tomcat.util.net.NioEndpoint$SocketProcessor.doRun(NioEndpoint.java:1791) at org.apache.tomcat.util.net.SocketProcessorBase.run(SocketProcessorBase.java:52) at org.apache.tomcat.util.threads.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1191) at org.apache.tomcat.util.threads.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:659) at org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61) at java.lang.Thread.run(Thread.java:750) Caused by: javax.net.ssl.SSLHandshakeException: PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target at sun.security.ssl.Alert.createSSLException(Alert.java:131) at sun.security.ssl.TransportContext.fatal(TransportContext.java:324) at sun.security.ssl.TransportContext.fatal(TransportContext.java:267) at sun.security.ssl.TransportContext.fatal(TransportContext.java:262) at sun.security.ssl.CertificateMessage$T12CertificateConsumer.checkServerCerts(CertificateMessage.java:654) at sun.security.ssl.CertificateMessage$T12CertificateConsumer.onCertificate(CertificateMessage.java:473) at sun.security.ssl.CertificateMessage$T12CertificateConsumer.consume(CertificateMessage.java:369) at sun.security.ssl.SSLHandshake.consume(SSLHandshake.java:377) at sun.security.ssl.HandshakeContext.dispatch(HandshakeContext.java:444) at sun.security.ssl.HandshakeContext.dispatch(HandshakeContext.java:422) at sun.security.ssl.TransportContext.dispatch(TransportContext.java:182) at sun.security.ssl.SSLTransport.decode(SSLTransport.java:152) at sun.security.ssl.SSLSocketImpl.decode(SSLSocketImpl.java:1397) at sun.security.ssl.SSLSocketImpl.readHandshakeRecord(SSLSocketImpl.java:1305) at sun.security.ssl.SSLSocketImpl.startHandshake(SSLSocketImpl.java:440) at com.microsoft.sqlserver.jdbc.TDSChannel.enableSSL(IOBuffer.java:1839) ... 38 more Caused by: sun.security.validator.ValidatorException: PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target at sun.security.validator.PKIXValidator.doBuild(PKIXValidator.java:456) at sun.security.validator.PKIXValidator.engineValidate(PKIXValidator.java:323) at sun.security.validator.Validator.validate(Validator.java:271) at sun.security.ssl.X509TrustManagerImpl.validate(X509TrustManagerImpl.java:315) at sun.security.ssl.X509TrustManagerImpl.checkTrusted(X509TrustManagerImpl.java:234) at sun.security.ssl.X509TrustManagerImpl.checkServerTrusted(X509TrustManagerImpl.java:110) at com.microsoft.sqlserver.jdbc.HostNameOverrideX509TrustManager.checkServerTrusted(SQLServerTrustManager.java:86) at sun.security.ssl.AbstractTrustManagerWrapper.checkServerTrusted(SSLContextImpl.java:1258) at sun.security.ssl.CertificateMessage$T12CertificateConsumer.checkServerCerts(CertificateMessage.java:638) ... 49 more Caused by: sun.security.provider.certpath.SunCertPathBuilderException: unable to find valid certification path to requested target at sun.security.provider.certpath.SunCertPathBuilder.build(SunCertPathBuilder.java:141) at sun.security.provider.certpath.SunCertPathBuilder.engineBuild(SunCertPathBuilder.java:126) at java.security.cert.CertPathBuilder.build(CertPathBuilder.java:280) at sun.security.validator.PKIXValidator.doBuild(PKIXValidator.java:451) ... 57 more怎么解决
> 
> 1 / 1

ChatGPTChatGPT

该错误提示是由于数据库连接驱动程序无法使用安全套接字层（SSL）加密与 SQL Server 建立安全连接所导致的。在 Java 应用程序中，可以尝试以下解决方案：

1.  检查 SQL Server 是否已启用 SSL 连接，如果没有，请在 SQL Server 上启用 SSL 连接。可以通过以下命令来启用 SQL Server SSL 连接：
    
    sql
    
    ```sql
    EXEC sp_configure 'network protocol', 1
    GO
    RECONFIGURE WITH OVERRIDE
    GO
    ```
    
2.  检查 Java 运行时环境是否有足够的信任证书来验证 SQL Server 的 SSL 证书。如果 Java 运行时环境不信任 SSL 证书，则会发生此错误。可以通过以下方式解决：
    
    a. 在 Java 运行时环境中导入 SQL Server SSL 证书。可以使用以下命令将 SQL Server SSL 证书导出为 ".cer" 格式：
    
    arduino
    
    ```arduino
    openssl s_client -connect yourserver:port -showcerts
    ```
    
    然后将导出的 ".cer" 文件导入到 Java 运行时环境中。
    
    b. 如果您使用的是较新的 Java 版本，您可以使用以下系统属性来解决此问题：
    
    diff
    
    ```diff
    -Djavax.net.ssl.trustStore=<path to truststore>
    -Djavax.net.ssl.trustStorePassword=<truststore password>
    ```
    
    这将在运行时设置信任库以验证 SSL 证书。
    
3.  如果您使用的是较旧的 Java 版本，则可能需要手动更新 Java 运行时环境的信任库。您可以使用以下命令来下载 SQL Server SSL 证书，并将其导入到 Java 运行时环境的信任库中：
    
    css
    
    ```css
    keytool -importcert -file <path to certificate file> -keystore <path to keystore>
    ```
    
    您需要替换 <path to certificate file> 和 <path to keystore> 为实际的路径。
    

希望这些解决方案能够帮助您解决该问题。

1 / 1

> 如何取消ssl认证
> 
> 1 / 1

ChatGPTChatGPT

取消SSL认证可能会存在安全风险，请谨慎操作。如果您仍然想要取消SSL认证，以下是一种可能的方法：

在Java代码中，取消SSL认证可以通过创建一个不验证证书的TrustManager来实现。具体步骤如下：

1.  创建一个不验证证书的TrustManager：

typescript

```typescript
TrustManager[] trustAllCerts = new TrustManager[] { new X509TrustManager() {
    public java.security.cert.X509Certificate[] getAcceptedIssuers() {
        return null;
    }

    public void checkClientTrusted(X509Certificate[] certs, String authType) {
    }

    public void checkServerTrusted(X509Certificate[] certs, String authType) {
    }
}};
```

2.  在建立连接时，使用该TrustManager：

java

```java
SSLContext sslContext = SSLContext.getInstance("SSL");
sslContext.init(null, trustAllCerts, new java.security.SecureRandom());

String connectionUrl = "jdbc:sqlserver://localhost:1433;databaseName=YourDB;integratedSecurity=true;encrypt=true;trustServerCertificate=false;hostNameInCertificate=*.yourdomain.com;sslProtocol=TLSv1.2";
Connection conn = DriverManager.getConnection(connectionUrl, "YourUser", "YourPassword");
```

注意，这种方法将取消对所有证书的验证，包括恶意证书。如果您需要取消SSL认证，请确保您信任连接的服务器。另外，取消SSL认证可能会违反您的组织或公司的安全策略，请在使用此方法之前咨询安全专业人员。

1 / 1