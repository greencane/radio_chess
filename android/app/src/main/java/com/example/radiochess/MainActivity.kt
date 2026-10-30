package com.example.radiochess

import android.annotation.SuppressLint
import android.app.Activity
import android.app.AlertDialog
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.JsResult
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.webkit.WebViewAssetLoader
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream

class MainActivity : Activity() {

    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.allowFileAccess = false
            settings.allowContentAccess = false
            webViewClient = object : WebViewClient() {
                override fun shouldInterceptRequest(
                    view: WebView,
                    request: WebResourceRequest
                ): WebResourceResponse? = assetLoader.shouldInterceptRequest(request.url)
            }
            webChromeClient = object : WebChromeClient() {
                override fun onJsConfirm(
                    view: WebView, url: String, message: String, result: JsResult
                ): Boolean {
                    AlertDialog.Builder(this@MainActivity)
                        .setMessage(message)
                        .setPositiveButton(android.R.string.ok) { _, _ -> result.confirm() }
                        .setNegativeButton(android.R.string.cancel) { _, _ -> result.cancel() }
                        .setOnCancelListener { result.cancel() }
                        .show()
                    return true
                }
            }
            addJavascriptInterface(GameStore(File(filesDir, "games")), "Native")
        }
        setContentView(webView)

        // Target SDK 35 draws edge-to-edge, so keep the page clear of system bars and keyboard.
        ViewCompat.setOnApplyWindowInsetsListener(webView) { v, insets ->
            val bars = insets.getInsets(
                WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.ime()
            )
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            WindowInsetsCompat.CONSUMED
        }

        webView.loadUrl("https://appassets.androidplatform.net/assets/index.html")
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }
}

/** Stores one PGN file per game plus active.txt, mirroring the desktop app's games folder. */
class GameStore(private val dir: File) {
    private val idPattern = Regex("[a-z0-9_-]+")

    init {
        dir.mkdirs()
    }

    private fun gameFile(id: String): File? =
        if (idPattern.matches(id)) File(dir, "$id.pgn") else null

    // Write to a temp file then rename, so a power loss can't corrupt the save.
    private fun atomicWrite(target: File, text: String) {
        val tmp = File(dir, target.name + ".tmp")
        FileOutputStream(tmp).use {
            it.write(text.toByteArray(Charsets.UTF_8))
            it.fd.sync()
        }
        if (!tmp.renameTo(target)) {
            target.delete()
            check(tmp.renameTo(target)) { "rename failed" }
        }
    }

    @JavascriptInterface
    fun listGames(): String {
        val out = JSONArray()
        dir.listFiles { f -> f.name.endsWith(".pgn") }?.forEach { f ->
            out.put(
                JSONObject()
                    .put("id", f.name.removeSuffix(".pgn"))
                    .put("mtime", f.lastModified())
                    .put("text", f.readText(Charsets.UTF_8))
            )
        }
        return out.toString()
    }

    @JavascriptInterface
    fun saveGame(id: String, text: String): Boolean {
        val f = gameFile(id) ?: return false
        return try {
            atomicWrite(f, text)
            true
        } catch (e: Exception) {
            false
        }
    }

    @JavascriptInterface
    fun deleteGame(id: String): Boolean = gameFile(id)?.delete() ?: false

    @JavascriptInterface
    fun getActive(): String {
        val f = File(dir, "active.txt")
        return if (f.exists()) f.readText(Charsets.UTF_8).trim() else ""
    }

    @JavascriptInterface
    fun setActive(id: String): Boolean = try {
        atomicWrite(File(dir, "active.txt"), id)
        true
    } catch (e: Exception) {
        false
    }
}
