from novel_bot.agent.mobius_adapter import run_outline

def main():
    print('CALLING_RUN_OUTLINE')
    try:
        run_outline('workspace/MOBIUS_TEST.yaml', output='mobius_test_output', dry_run=True, end_chapter=3)
        print('RUN_OK')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('RUN_ERROR', e)

if __name__ == '__main__':
    main()
