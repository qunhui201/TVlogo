      # 7. 若有更新则保存到 history 目录并加简化命名
      - name: Save updated M3U and TVBox files with simplified names
        if: env.no_change == 'false'
        run: |
          TIMESTAMP=$(date +"%m%d%H%M")
          mkdir -p history
          # 保存原来的 m3u 文件
          cp output.m3u history/${TIMESTAMP}.m3u
          cp output_with_logo.m3u history/logo${TIMESTAMP}.m3u
          # 保存 TVBox 输出文件
          cp tvbox_output.txt history/tvbox_${TIMESTAMP}.txt
          echo "✅ 已保存到："
          echo " - history/${TIMESTAMP}.m3u"
          echo " - history/logo${TIMESTAMP}.m3u"
          echo " - history/tvbox_${TIMESTAMP}.txt"

      # 8. 上传 artifact（仅当有更新）
      - name: Upload M3U and TVBox files as artifact
        if: env.no_change == 'false'
        uses: actions/upload-artifact@v4
        with:
          name: m3u-playlist-${{ github.run_id }}
          path: |
            output.m3u
            output_with_logo.m3u
            tvbox_output.txt
